"""
THE ORCHESTRATOR — the "brain" of FinPilot.

A real MCP client: connects to our own MCP server, asks it what tools exist,
hands those tools to Claude, and runs the standard agentic loop:

    ask Claude -> Claude requests a tool -> we call it via MCP -> feed the
    result back to Claude -> repeat until Claude has enough to answer.

`run_chat_stream` is an async generator yielding small dict events as the
loop runs. Every real hop between the four parties is emitted as a `trace`
event so the frontend can draw a live sequence diagram of the MCP
architecture during the demo:

    app  ->  orchestrator  ->  claude (Messages API)
                           ->  mcp (MCP server -> portal APIs)

Trace event shape:
    {"type": "trace", "seq": 3, "ms": 412, "turn": 1,
     "kind": "tool_call", "from": "orchestrator", "to": "mcp",
     "label": "tools/call get_banking_accounts", "detail": {...}}

The stream ends with one `final` event (reply text, tool-call list, any
proposal, and run totals) or an `error` event from the router.
"""
import json
import time
import anthropic
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from app.core.config import settings

MODEL = "claude-sonnet-4-5"

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
PREVIEW_CHARS = 1200


def _mcp_tool_to_anthropic_schema(tool) -> dict:
    return {
        "name": tool.name,
        "description": tool.description or "",
        "input_schema": tool.input_schema,
    }


def _preview(text: str) -> str:
    """Pretty-print JSON results for the trace view, trimmed for the wire."""
    try:
        text = json.dumps(json.loads(text), indent=2)
    except (json.JSONDecodeError, TypeError):
        pass
    return text if len(text) <= PREVIEW_CHARS else text[:PREVIEW_CHARS] + "\n…"


class _Tracer:
    """Numbers and timestamps trace events relative to the start of the run."""

    def __init__(self):
        self.start = time.perf_counter()
        self.seq = 0

    def ms(self) -> int:
        return int((time.perf_counter() - self.start) * 1000)

    def event(self, kind, frm, to, label, detail=None, turn=None, duration_ms=None) -> dict:
        self.seq += 1
        ev = {
            "type": "trace",
            "seq": self.seq,
            "ms": self.ms(),
            "kind": kind,
            "from": frm,
            "to": to,
            "label": label,
        }
        if detail is not None:
            ev["detail"] = detail
        if turn is not None:
            ev["turn"] = turn
        if duration_ms is not None:
            ev["duration_ms"] = duration_ms
        return ev


async def run_chat_stream(user_message: str, max_turns: int = 6):
    """Async generator yielding trace events, ending with a 'final' event
    containing the reply text, the tool-call list, run totals, and (if the
    LLM invoked the proposal tool with a recommendation) a structured
    `proposal` the UI can render as a confirm/execute card."""
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    tr = _Tracer()
    tool_trace: list[dict] = []
    proposal = None
    totals = {"input_tokens": 0, "output_tokens": 0, "claude_calls": 0, "tool_calls": 0}

    yield tr.event(
        "request", "app", "orchestrator", "POST /orchestrator (SSE stream)",
        detail={"user_message": user_message},
    )

    mcp_url = f"{settings.INTERNAL_URL}/mcp/"
    async with streamable_http_client(mcp_url) as (read, write):
        async with ClientSession(read, write) as session:
            t0 = time.perf_counter()
            init = await session.initialize()
            yield tr.event(
                "mcp_init", "orchestrator", "mcp", "MCP initialize",
                detail={
                    "server_url": mcp_url,
                    "transport": "Streamable HTTP",
                    "server_name": init.server_info.name,
                    "protocol_version": init.protocol_version,
                },
                duration_ms=int((time.perf_counter() - t0) * 1000),
            )

            t0 = time.perf_counter()
            tools_result = await session.list_tools()
            tool_names = [t.name for t in tools_result.tools]
            yield tr.event(
                "mcp_tools_list", "mcp", "orchestrator", f"tools/list → {len(tool_names)} tools",
                detail={"tools": tool_names},
                duration_ms=int((time.perf_counter() - t0) * 1000),
            )
            anthropic_tools = [_mcp_tool_to_anthropic_schema(t) for t in tools_result.tools]

            messages = [{"role": "user", "content": user_message}]

            last_results = 0  # tool_result blocks being sent back on this turn

            for turn in range(1, max_turns + 1):
                yield tr.event(
                    "llm_request", "orchestrator", "claude", f"messages.create · turn {turn}",
                    turn=turn,
                    detail={
                        "model": MODEL,
                        "tools_offered": len(anthropic_tools),
                        "messages_in_context": len(messages),
                        "tool_results_included": last_results,
                        "note": "Sends the user question + all MCP tool schemas"
                        if turn == 1 else "Sends the tool results back so Claude can continue",
                    },
                )

                t0 = time.perf_counter()
                response = await client.messages.create(
                    model=MODEL,
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=anthropic_tools,
                    messages=messages,
                )
                llm_ms = int((time.perf_counter() - t0) * 1000)
                totals["claude_calls"] += 1
                totals["input_tokens"] += response.usage.input_tokens
                totals["output_tokens"] += response.usage.output_tokens

                requested = [b for b in response.content if b.type == "tool_use"]
                said = "".join(b.text for b in response.content if b.type == "text").strip()

                if response.stop_reason == "tool_use":
                    label = f"tool_use → {', '.join(b.name for b in requested)}"
                else:
                    label = f"{response.stop_reason} → final answer"
                yield tr.event(
                    "llm_response", "claude", "orchestrator", label,
                    turn=turn, duration_ms=llm_ms,
                    detail={
                        "stop_reason": response.stop_reason,
                        "tools_requested": [{"name": b.name, "input": b.input} for b in requested],
                        "claude_text": said or None,
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                )

                if response.stop_reason != "tool_use":
                    yield tr.event(
                        "final", "orchestrator", "app", "Render answer to user",
                        detail={"chars": len(said)},
                    )
                    yield {
                        "type": "final",
                        "reply": said,
                        "tool_calls": tool_trace,
                        "proposal": proposal,
                        "totals": {**totals, "total_ms": tr.ms(), "turns": turn},
                    }
                    return

                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in requested:
                    yield tr.event(
                        "tool_call", "orchestrator", "mcp", f"tools/call {block.name}",
                        turn=turn,
                        detail={"tool": block.name, "arguments": block.input, "tool_use_id": block.id},
                    )
                    t0 = time.perf_counter()
                    result = await session.call_tool(block.name, block.input)
                    tool_ms = int((time.perf_counter() - t0) * 1000)
                    totals["tool_calls"] += 1

                    result_text = result.content[0].text if result.content else "{}"
                    is_error = bool(result.is_error) or '"error"' in result_text[:200]
                    tool_trace.append({"tool": block.name, "input": block.input, "result": result_text})
                    yield tr.event(
                        "tool_result", "mcp", "orchestrator",
                        f"{block.name} → {len(result_text):,} bytes" + (" (error)" if is_error else ""),
                        turn=turn, duration_ms=tool_ms,
                        detail={"tool": block.name, "is_error": is_error, "result_preview": _preview(result_text)},
                    )

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
                last_results = len(tool_results)

            yield tr.event("final", "orchestrator", "app", "Stopped: turn limit reached")
            yield {
                "type": "final",
                "reply": "I wasn't able to finish gathering everything I needed — try asking again.",
                "tool_calls": tool_trace,
                "proposal": proposal,
                "totals": {**totals, "total_ms": tr.ms(), "turns": max_turns},
            }
