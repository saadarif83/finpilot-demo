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

    # Frontend URL, used for CORS. Set to your Vercel URL in production (no trailing slash).
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # This backend's own PUBLIC URL — used ONLY for things the user's browser
    # must reach directly (OAuth redirect URIs shown in the address bar).
    # Set this to your Render URL once deployed (no trailing slash).
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    # This backend calling ITSELF (MCP client -> MCP server, internal token
    # exchanges, internal portal reads/writes) must NOT go out to the public
    # internet and back in — many platforms (Render included) don't support a
    # service looping back to its own public hostname, which causes a silent
    # connection failure. Same process, so localhost is correct and reliable.
    PORT: str = os.getenv("PORT", "8000")
    INTERNAL_URL: str = os.getenv("INTERNAL_URL", f"http://localhost:{PORT}")


settings = Settings()
