# FinPilot — Conference Demo

A simulated multi-portal personal finance app. FinPilot (an LLM orchestrator)
authenticates against 4 fake financial "portals" using different real-world
auth mechanisms, pulls data from each, and answers questions like "should I
make an extra mortgage payment?"

## Repo layout

```
finpilot/
├── backend/                    <- ONE FastAPI service, deploy this to Render
│   ├── requirements.txt
│   └── app/
│       ├── main.py             <- FastAPI app entrypoint, mounts all routers
│       ├── core/
│       │   ├── config.py       <- env vars / settings
│       │   └── security.py     <- shared JWT issue/verify helpers
│       ├── portals/            <- one file per simulated financial portal
│       │   ├── banking.py      <- OAuth 2.0 Authorization Code flow (DONE - Day 1)
│       │   ├── banking_data.py <- fake accounts/transactions
│       │   ├── mortgage.py     <- OIDC flow (Day 2)
│       │   ├── creditcard.py   <- Client Credentials flow (Day 2)
│       │   └── brokerage.py    <- Open-Banking-style consent flow (Day 2)
│       ├── mcp_servers/        <- MCP tool servers wrapping the portals (Day 3)
│       └── orchestrator/       <- Claude + MCP client, the "brain" (Day 4)
└── frontend/                   <- React PWA, deploy this to Vercel (Day 5-6)
```

## Running the backend locally

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/portals/banking/authorize?client_id=finpilot&redirect_uri=http://localhost:5173/callback&state=abc
to see the simulated bank's login/consent screen. Login with `demo` / `demo123`.

## What's done vs. what's next

- [x] Day 1: repo scaffold, banking portal (OAuth 2.0 Authorization Code), tested end-to-end
- [ ] Day 2: mortgage (OIDC), credit card (Client Credentials), brokerage (consent flow)
- [ ] Day 3: MCP servers
- [ ] Day 4: orchestrator (Claude + MCP)
- [ ] Day 5-6: PWA frontend + deploy
