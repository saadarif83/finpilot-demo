import json
import anthropic
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.config import settings
from app.orchestrator.agent import run_chat_stream, ADVICE_PROMPT

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


class ChatRequest(BaseModel):
    message: str


def _sse_line(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


async def _stream_events(message: str):
    """Wraps run_chat_stream so any mid-stream exception becomes a clean
    'error' SSE event instead of a broken connection or a raw traceback —
    important for a live demo where the connection must never just die
    silently on stage."""
    try:
        async for event in run_chat_stream(message):
            yield _sse_line(event)
    except anthropic.APIError as e:
        yield _sse_line({"type": "error", "message": f"Claude API error: {e}"})
    except Exception as e:
        yield _sse_line({"type": "error", "message": f"Orchestrator error: {e}"})


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(500, "ANTHROPIC_API_KEY is not configured on the backend.")
    return StreamingResponse(_stream_events(req.message), media_type="text/event-stream")


@router.post("/advice/stream")
async def advice_stream():
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(500, "ANTHROPIC_API_KEY is not configured on the backend.")
    return StreamingResponse(_stream_events(ADVICE_PROMPT), media_type="text/event-stream")


@router.post("/chat")
async def chat(req: ChatRequest):
    """Non-streaming convenience endpoint — collects the stream and returns
    the final result in one response. Kept for simple/manual testing."""
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(500, "ANTHROPIC_API_KEY is not configured on the backend.")
    final = None
    try:
        async for event in run_chat_stream(req.message):
            if event["type"] == "final":
                final = event
    except anthropic.APIError as e:
        raise HTTPException(502, f"Claude API error: {e}")
    except Exception as e:
        raise HTTPException(500, f"Orchestrator error: {e}")
    return final
