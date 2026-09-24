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
│       ├── mcp_servers/
│       │   └── finpilot_mcp.py <- MCP server: all 4 portals + market news as tools (DONE - Day 3)
│       ├── connect.py          <- generic "connect account" flow: drives each portal's OAuth, stores tokens (DONE - Day 3)
│       └── orchestrator/
│           ├── agent.py        <- Claude as an MCP client, agentic tool-use loop (DONE - Day 4)
│           └── router.py       <- POST /orchestrator/chat endpoint (DONE - Day 4)
└── frontend/                   <- React PWA (DONE - Day 5-6), deploy to Vercel
    ├── src/
    │   ├── App.jsx              <- tab switcher: Accounts / Chat
    │   ├── api.js                <- talks to the backend
    │   └── components/
    │       ├── ConnectScreen.jsx <- 4 portal cards with auth-mechanism badges
    │       └── ChatScreen.jsx    <- chat UI, shows which tools got called per answer
    └── public/
        ├── manifest.json         <- PWA manifest (installable to home screen)
        └── sw.js                 <- minimal service worker
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

## How to "connect" an account (Day 3 flow)

Instead of hitting each portal's `/authorize` directly, the app now uses one
consistent entry point per portal:

```
GET  /connect/banking       -> redirects through the bank's login screen, stores the token on success
GET  /connect/mortgage      -> same, via OIDC
GET  /connect/brokerage     -> same, via PKCE (verifier handled server-side)
POST /connect/creditcard    -> no redirect; fetches a Client Credentials token directly
GET  /connect/status        -> { "connected": ["banking", "creditcard", ...] }
```

## MCP server

All connected portals are exposed as MCP tools at `/mcp` (Streamable HTTP transport):
`get_banking_accounts`, `get_banking_transactions`, `get_mortgage_details`,
`get_creditcard_account`, `get_creditcard_transactions`, `get_brokerage_positions`,
`get_brokerage_cash`, `get_market_news`. If a portal isn't connected yet, its
tool returns a clear error message instead of crashing — the orchestrator LLM
can use that to tell the user what to connect next.

**Note:** if you deploy this to Render, set the `BACKEND_URL` env var to your
Render URL (e.g. `https://finpilot-backend.onrender.com`) — the connect flow
and MCP tools call the backend's own portal endpoints using this URL.

## What's done vs. what's next

- [x] Day 1: repo scaffold, banking portal (OAuth 2.0 Authorization Code), tested end-to-end
- [x] Day 2: mortgage (OIDC), credit card (Client Credentials), brokerage (Authorization Code + PKCE) — all tested end-to-end
- [x] Day 3: MCP server (8 tools across all 4 portals + market news), generic connect flow, tested end-to-end including the full connect → token → MCP tool call chain
- [x] Day 4: orchestrator — Claude as a real MCP client, agentic tool-use loop, verified (schema conversion, clean error handling when key missing/bad). **You'll do the final live-response check yourself once your ANTHROPIC_API_KEY is in place.**
- [x] Day 5-6: PWA frontend (Accounts + Chat screens), verified: builds cleanly, CORS confirmed working
- [ ] Day 7: rehearsal — see checklist below

## Deploying Day 4-6

**Backend (Render) — add these env vars** to the same service from before:
- `ANTHROPIC_API_KEY` — your key from console.anthropic.com
- `FINNHUB_API_KEY` — optional; without it, market news uses realistic sample data (never breaks the demo)

**Frontend (Vercel):**
1. Push the `frontend/` folder to your GitHub repo the same way as before
2. Go to vercel.com → sign in with GitHub → **Add New → Project** → select your repo
3. **Root Directory:** `frontend`
4. Framework preset should auto-detect as Vite
5. Add environment variable: `VITE_BACKEND_URL` = your Render backend URL (e.g. `https://finpilot-backend.onrender.com`)
6. Deploy — you'll get a URL like `finpilot-demo.vercel.app`
7. **Also add `finpilot-demo.vercel.app` to the backend's `FRONTEND_ORIGIN` env var on Render** (no trailing slash), so CORS allows it — then redeploy the backend

**On your phone:** open the Vercel URL in Safari/Chrome, then "Add to Home Screen" — it'll open full-screen like a real app for the demo.

## Day 7 checklist — before you go on stage

- [ ] Load the app on your actual demo phone, added to home screen, at least the night before
- [ ] **Ping the Render backend 5-10 minutes before your talk** (visit its URL once) — free tier sleeps after 15 min idle and takes ~30-50s to wake, you don't want that lag live
- [ ] Connect all 4 accounts fresh and confirm each shows "✓ Connected"
- [ ] Run all 3 demo questions once end-to-end and time them
- [ ] Have a **backup plan**: screen-record a successful run beforehand in case live wifi/venue network fails
- [ ] Double check `ANTHROPIC_API_KEY` and `FRONTEND_ORIGIN`/`VITE_BACKEND_URL` are all correctly set — a typo here is the most likely last-minute breakage
- [ ] If presenting on venue wifi, consider using your phone's hotspot instead — conference wifi is notoriously unreliable for live demos
