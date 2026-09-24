"""
THE ORCHESTRATOR — the "brain" of FinPilot.

This is a real MCP client: it connects to our own MCP server (the same one
built in Day 3, wrapping all 4 portals + market news), asks it what tools
exist, hands those tools to Claude, and runs the standard agentic loop:

    ask Claude -> Claude requests a tool -> we call it via MCP -> feed the
    result back to Claude -> repeat until Claude has enough to answer.

Claude decides WHICH accounts it needs to look at for a given question — we
never hardcode "always check banking + brokerage". Ask about a mortgage
payoff and it may only call the mortgage and banking tools; ask about a
vacation and it may pull banking, credit card, and brokerage.
"""
import anthropic
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from app.core.config import settings

SYSTEM_PROMPT = """You are FinPilot, a personal AI financial advisor. You have tools to read \
the user's connected banking, mortgage, credit card, and brokerage accounts, plus real-time \
market news. Use the tools to gather whatever real data you need before answering — never \
guess or make up numbers. If a needed account isn't connected yet, tell the user clearly which \
one to connect. Give a direct recommendation (not just a data dump): should they spend, save, \
invest, or pay down debt, and why, backed by the actual numbers you pulled. Keep answers \
concise and conversational, suitable for reading on a phone."""


def _mcp_tool_to_anthropic_schema(tool) -> dict:
    return {
        "name": tool.name,
        "description": tool.description or "",
        "input_schema": tool.input_schema,
    }


async def run_chat(user_message: str, max_turns: int = 6) -> dict:
    """Runs one full agentic turn: returns the final reply text plus a trace
    of which tools were called, so the demo UI can show its work."""
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    tool_trace: list[dict] = []

    async with streamable_http_client(f"{settings.INTERNAL_URL}/mcp/") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            anthropic_tools = [_mcp_tool_to_anthropic_schema(t) for t in tools_result.tools]

            messages = [{"role": "user", "content": user_message}]

            for _ in range(max_turns):
                response = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=anthropic_tools,
                    messages=messages,
                )

                if response.stop_reason != "tool_use":
                    final_text = "".join(b.text for b in response.content if b.type == "text")
                    return {"reply": final_text, "tool_calls": tool_trace}

                # Claude wants to call one or more tools. Execute each via MCP,
                # then feed the results back in the next turn.
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    result = await session.call_tool(block.name, block.input)
                    result_text = result.content[0].text if result.content else "{}"
                    tool_trace.append({"tool": block.name, "input": block.input, "result": result_text})
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })
                messages.append({"role": "user", "content": tool_results})

            return {"reply": "I wasn't able to finish gathering everything I needed — try asking again.", "tool_calls": tool_trace}
