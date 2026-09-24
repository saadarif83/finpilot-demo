from contextlib import asynccontextmanager, AsyncExitStack
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.portals.banking import router as banking_router
from app.portals.mortgage import router as mortgage_router
from app.portals.creditcard import router as creditcard_router
from app.portals.brokerage import router as brokerage_router
from app.connect import router as connect_router
from app.orchestrator.router import router as orchestrator_router
from app.mcp_servers.finpilot_mcp import mcp_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The MCP server has its own internal session manager that needs its
    # lifespan started explicitly — FastAPI's app.mount() alone does NOT do
    # this for a mounted sub-app, which silently breaks every MCP request
    # with "Task group is not initialized" until this is wired up.
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(mcp_app.router.lifespan_context(mcp_app))
        yield


app = FastAPI(title="FinPilot Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(banking_router)
app.include_router(mortgage_router)
app.include_router(creditcard_router)
app.include_router(brokerage_router)
app.include_router(connect_router)
app.include_router(orchestrator_router)
app.mount("/mcp", mcp_app)


@app.get("/")
def health():
    return {"status": "ok", "service": "finpilot-backend"}
