import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Secret used to sign JWTs issued by ALL simulated portals.
    # In real life each bank would have its own key — for the demo one shared
    # secret keeps things simple. Set this in Render's env vars in production.
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-only-secret-change-me")
    JWT_ALGORITHM: str = "HS256"

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")

    # Frontend URL, used for CORS. Set to your Vercel URL in production.
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

settings = Settings()
