# FinPilot — Conference Demo

A simulated multi-portal personal finance app. FinPilot (an LLM orchestrator)
authenticates against 4 fake financial "portals" using different real-world
auth mechanisms, pulls data from each, shows a unified dashboard, gives
proactive AI advice, and — with your explicit confirmation — can execute a
recommended action across two portals at once.

## Repo layout

```
finpilot/
├── backend/                        <- ONE FastAPI service, deploy to Render
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 <- FastAPI app entrypoint, mounts all routers
│       ├── core/
│       │   ├── config.py           <- env vars / settings (BACKEND_URL vs INTERNAL_URL — see note below)
│       │   ├── security.py         <- shared JWT issue/verify helpers
│       │   └── token_store.py      <- in-memory per-portal token vault
│       ├── portals/                <- one file per simulated financial portal
│       │   ├── banking.py / banking_data.py        <- OAuth 2.0 Authorization Code
│       │   ├── mortgage.py / mortgage_data.py       <- OpenID Connect (discovery doc + ID token)
│       │   ├── creditcard.py / creditcard_data.py   <- OAuth2 Client Credentials (machine-to-machine)
│       │   └── brokerage.py / brokerage_data.py     <- Authorization Code + PKCE
│       ├── connect.py              <- generic "connect account" flow, drives each portal's OAuth
│       ├── dashboard.py            <- aggregated summary + drill-down detail proxies
│       ├── actions.py              <- DETERMINISTIC action executor (see Agentic Action Safety below)
│       ├── mcp_servers/
│       │   └── finpilot_mcp.py     <- MCP server: read-only tools + the payoff proposal calculator
│       └── orchestrator/
│           ├── agent.py            <- Claude as an MCP client; streams progress events
│           └── router.py           <- /orchestrator/chat, /chat/stream, /advice/stream
└── frontend/                        <- React PWA, deploy to Vercel
    ├── src/
    │   ├── App.jsx                  <- shell: header w/ connection badges, dashboard-first, tab bar
    │   ├── api.js                   <- backend client incl. SSE streaming helper
    │   ├── colors.js                <- validated chart palette (see Chart Design below)
    │   └── components/
    │       ├── Dashboard.jsx        <- single-pane-of-glass overview cards + net position
    │       ├── DetailView.jsx       <- drill-down modal, picks the right chart per account
    │       ├── charts/              <- CashflowChart, SpendingBreakdown, PerformanceChart, AmortizationChart
    │       ├── AdvicePanel.jsx       <- "Ask FinPilot for advice" flow, live activity feed + proposal
    │       ├── ChatScreen.jsx        <- free-form chat, same live activity feed + proposal
    │       ├── ActivityFeed.jsx      <- live "what FinPilot is doing" step tracker (demo-friendly)
    │       ├── ProposalCard.jsx      <- confirm/execute UI for the agentic action
    │       └── ConnectModal.jsx      <- the 4 portal connect cards, now a modal (not the home screen)
    └── public/                       <- PWA manifest, service worker, icon
```

## Running locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env   # VITE_BACKEND_URL=http://localhost:8000
npm run dev
```

## Auth mechanisms implemented (talk content)

| Portal | Mechanism | Real-world analog |
|---|---|---|
| Banking | OAuth 2.0 Authorization Code | Plaid, most bank APIs |
| Mortgage | OpenID Connect | Okta/Auth0/Azure AD B2C-backed lenders |
| Credit Card | OAuth 2.0 Client Credentials | Machine-to-machine / API-key integrations |
| Brokerage | Authorization Code + PKCE | Required pattern for public/mobile clients |

Login with `demo` / `demo123` on banking, mortgage, and brokerage. Credit card
has no login screen — it's server-to-server only, by design.

## BACKEND_URL vs INTERNAL_URL — an important gotcha

Two different settings, two different jobs:
- **`BACKEND_URL`** — the backend's *public* URL. Used ONLY for OAuth redirect
  URIs the user's browser must reach directly.
- **`INTERNAL_URL`** — defaults to `http://localhost:$PORT`. Used for every
  server-to-server call the backend makes to itself (MCP client → MCP server,
  token exchanges, portal reads/writes).

**Do not merge these.** Render (and most PaaS hosts) don't reliably support a
service calling its own public hostname from inside itself — it goes out to
the internet and often never comes back in, causing a silent `TaskGroup`
connection failure. `INTERNAL_URL` avoids that by staying on localhost, since
it's all the same process anyway.

## Agentic action safety — how #3 (pay off credit card from brokerage cash) works

This is the one place in the app that moves money, so it's built with a
hard boundary between **reasoning** and **execution**:

1. The LLM can call `propose_creditcard_payoff_from_brokerage` — a READ-ONLY
   MCP tool that checks the card's APR against idle brokerage cash, computes
   a recommended amount (keeping a cash buffer), and returns a structured
   plan. It never touches a portal's write endpoint.
2. The orchestrator extracts this plan and returns it as a `proposal` object
   alongside the chat reply — the UI renders it as a `ProposalCard` with the
   before/after numbers and an explicit **"Confirm & Execute"** button.
3. Only a human clicking that button calls `POST /actions/execute` — a
   completely separate endpoint with **no MCP tool wired to it**, so the LLM
   has no path to ever call it directly, no matter how a prompt is phrased.
4. `/actions/execute` performs the two writes (brokerage withdraw → credit
   card payment) with compensation: if the second write fails after the
   first succeeded, it automatically refunds the brokerage withdrawal so the
   two portals never end up inconsistent. Verified by a real test that
   disconnects the credit card mid-flow and confirms the refund fires.

This mirrors a real brokerage's "review order → confirm → execute" pattern,
and is good material for the OAuth-security-model section of the talk: a
model should never be one ambiguous sentence away from moving money.

## Live activity feed (streaming)

`/orchestrator/chat/stream` and `/orchestrator/advice/stream` return
Server-Sent Events, not a single JSON blob — each tool call and status update
streams to the frontend as it happens, rendered by `ActivityFeed.jsx`. This
is what makes the MCP architecture visible during the demo: the audience
watches FinPilot decide which accounts to check, in real time, rather than
staring at a spinner. If the LLM call fails mid-stream (bad key, network
blip), it degrades to a clean `error` event — verified by testing with a
deliberately invalid API key, never a raw crash.

## Chart design

Charts follow a validated colorblind-safe palette (fixed categorical hue
order, single-hue sequential ramps, tooltips + legends on every multi-series
chart, color assigned by category *identity* not sorted rank — see
`frontend/src/colors.js`). Credit card spending uses a horizontal bar chart
rather than a pie, since bar length compares 6 categories more precisely
than slice angle.

## Deploying

**Backend (Render):**
1. New Web Service → connect your GitHub repo → root directory `backend`
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Env vars: `JWT_SECRET` (any random string), `ANTHROPIC_API_KEY`,
   `FINNHUB_API_KEY` (optional — falls back to sample news), `FRONTEND_ORIGIN`
   (your Vercel URL, **no trailing slash**), `BACKEND_URL` (this service's own
   Render URL, **no trailing slash**)

**Frontend (Vercel):**
1. New Project → same repo → root directory `frontend` → framework Vite
2. Env var: `VITE_BACKEND_URL` = your Render backend URL (no trailing slash)
3. On your phone: open the Vercel URL, "Add to Home Screen"

**After deploying either side**, double-check both `FRONTEND_ORIGIN` (Render)
and `VITE_BACKEND_URL` (Vercel) have no trailing slash — a trailing slash
breaks CORS matching and produces double-slash API paths respectively.

## Day-of-talk checklist

- [ ] Ping the Render backend 5–10 min before going on stage (free tier
      sleeps after 15 min idle; cold start takes 30–50s)
- [ ] Reconnect all 4 accounts fresh (token store is in-memory, resets on
      every backend restart/redeploy)
- [ ] Run through: Dashboard overview → drill into 2-3 accounts → tap
      "Ask FinPilot for advice" → confirm the payoff proposal if it appears →
      ask 1-2 free-form chat questions
- [ ] Have a backup screen recording in case of venue wifi issues
- [ ] Use your phone's hotspot instead of conference wifi if possible
