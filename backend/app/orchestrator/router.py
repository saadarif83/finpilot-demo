from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import anthropic
from app.core.config import settings
from app.orchestrator.agent import run_chat

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(req: ChatRequest):
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(500, "ANTHROPIC_API_KEY is not configured on the backend.")
    try:
        return await run_chat(req.message)
    except anthropic.APIError as e:
        # Never let a raw stack trace reach the stage during a live demo.
        raise HTTPException(502, f"Claude API error: {e}")
    except Exception as e:
        raise HTTPException(500, f"Orchestrator error: {e}")
