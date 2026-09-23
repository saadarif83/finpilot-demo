from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.portals.banking import router as banking_router
from app.portals.mortgage import router as mortgage_router
from app.portals.creditcard import router as creditcard_router
from app.portals.brokerage import router as brokerage_router

app = FastAPI(title="FinPilot Backend")

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


@app.get("/")
def health():
    return {"status": "ok", "service": "finpilot-backend"}
