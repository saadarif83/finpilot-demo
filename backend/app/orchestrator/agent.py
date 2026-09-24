"""
THE ORCHESTRATOR — the "brain" of FinPilot.

A real MCP client: connects to our own MCP server, asks it what tools exist,
hands those tools to Claude, and runs the standard agentic loop:

    ask Claude -> Claude requests a tool -> we call it via MCP -> feed the
    result back to Claude -> repeat until Claude has enough to answer.

`run_chat_stream` is an async generator yielding small dict "events" as the
loop progresses (status / tool_call / tool_result / final). The router turns
these into Server-Sent Events so the frontend can show a live "what FinPilot
is doing right now" activity feed during the call — good demo material, and
genuinely useful for debugging which accounts got checked for a given answer.
"""
import json
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
concise and conversational, suitable for reading on a phone.

If paying down credit card debt from idle brokerage cash looks like a good move, use the \
propose_creditcard_payoff_from_brokerage tool to compute a concrete plan rather than estimating \
the numbers yourself, and mention in your reply that you've put together a proposal they can \
review and confirm."""

ADVICE_PROMPT = """Give me a quick daily briefing on my finances. Check my connected accounts, \
tell me anything that stands out (low cash, high credit utilization, idle brokerage cash, a \
good rate on my mortgage vs market, etc.), and give me one clear top recommendation for what to \
do today. If paying down credit card debt from idle brokerage cash is a good move, propose it."""

PROPOSAL_TOOL_NAME = "propose_creditcard_payoff_from_brokerage"


def _mcp_tool_to_anthropic_schema(tool) -> dict:
    return {
        "name": tool.name,
        "description": tool.description or "",
        "input_schema": tool.input_schema,
    }


async def run_chat_stream(user_message: str, max_turns: int = 6):
    """Async generator yielding progress events, ending with a 'final' event
    containing the reply text, the full tool-call trace, and (if the LLM
    invoked the proposal tool with a recommendation) a structured `proposal`
    the UI can render as a confirm/execute card."""
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    tool_trace: list[dict] = []
    proposal = None

    yield {"type": "status", "message": "Connecting to your connected accounts..."}

    async with streamable_http_client(f"{settings.INTERNAL_URL}/mcp/") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            anthropic_tools = [_mcp_tool_to_anthropic_schema(t) for t in tools_result.tools]

            messages = [{"role": "user", "content": user_message}]

            for _ in range(max_turns):
                yield {"type": "status", "message": "Thinking..."}
                response = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=anthropic_tools,
                    messages=messages,
                )

                if response.stop_reason != "tool_use":
                    final_text = "".join(b.text for b in response.content if b.type == "text")
                    yield {
                        "type": "final",
                        "reply": final_text,
                        "tool_calls": tool_trace,
                        "proposal": proposal,
                    }
                    return

                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    yield {"type": "tool_call", "tool": block.name, "input": block.input}
                    result = await session.call_tool(block.name, block.input)
                    result_text = result.content[0].text if result.content else "{}"
                    tool_trace.append({"tool": block.name, "input": block.input, "result": result_text})
                    yield {"type": "tool_result", "tool": block.name, "result": result_text}

                    if block.name == PROPOSAL_TOOL_NAME:
                        try:
                            parsed = json.loads(result_text)
                            if parsed.get("recommended"):
                                proposal = parsed
                        except (json.JSONDecodeError, TypeError):
                            pass

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })
                messages.append({"role": "user", "content": tool_results})

            yield {
                "type": "final",
                "reply": "I wasn't able to finish gathering everything I needed — try asking again.",
                "tool_calls": tool_trace,
                "proposal": proposal,
            }
