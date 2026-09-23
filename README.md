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
│       │   ├── mortgage.py     <- OpenID Connect: discovery doc + ID token (DONE - Day 2)
│       │   ├── mortgage_data.py
│       │   ├── creditcard.py   <- OAuth2 Client Credentials, machine-to-machine (DONE - Day 2)
│       │   ├── creditcard_data.py
│       │   ├── brokerage.py    <- OAuth2 Authorization Code + PKCE (DONE - Day 2)
│       │   └── brokerage_data.py
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

## Auth mechanisms implemented (talk content)

| Portal | Mechanism | Why this one | Real-world analog |
|---|---|---|---|
| Banking | OAuth 2.0 Authorization Code | Standard delegated access, confidential client | Plaid, most bank APIs |
| Mortgage | OpenID Connect | Adds an identity layer (ID token) on top of OAuth2 | Okta/Auth0/Azure AD B2C-backed lenders |
| Credit Card | OAuth 2.0 Client Credentials | Machine-to-machine, no user redirect | Merchant/API-key integrations |
| Brokerage | Authorization Code + PKCE | Required for public/mobile clients that can't hold a secret | How a real mobile app *must* do OAuth |

## Try each portal's login screen locally

```
http://localhost:8000/portals/banking/authorize?client_id=finpilot&redirect_uri=http://localhost:5173/callback&state=abc
http://localhost:8000/portals/mortgage/authorize?client_id=finpilot&redirect_uri=http://localhost:5173/callback&state=abc
http://localhost:8000/portals/brokerage/authorize?client_id=finpilot&redirect_uri=http://localhost:5173/callback&state=abc&code_challenge=TVcrHRs8gZPA2G10D83R3eToeSLQ20OLKL-oBbl6GYg
```
(Credit card has no login screen — it's server-to-server only, by design.)
Login with `demo` / `demo123` on all three.

## What's done vs. what's next

- [x] Day 1: repo scaffold, banking portal (OAuth 2.0 Authorization Code), tested end-to-end
- [x] Day 2: mortgage (OIDC), credit card (Client Credentials), brokerage (Authorization Code + PKCE) — all tested end-to-end
- [ ] Day 3: MCP servers
- [ ] Day 4: orchestrator (Claude + MCP)
- [ ] Day 5-6: PWA frontend + deploy
