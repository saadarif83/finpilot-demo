const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export async function getConnectStatus() {
  const res = await fetch(`${BACKEND_URL}/connect/status`);
  if (!res.ok) throw new Error("Failed to load connection status");
  return res.json();
}

export function openConnectPopup(portal) {
  const url = `${BACKEND_URL}/connect/${portal}`;
  return window.open(url, "connect", "width=380,height=560");
}

export async function connectCreditCard() {
  const res = await fetch(`${BACKEND_URL}/connect/creditcard`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to connect credit card");
  return res.json();
}

// Demo shortcut: the backend runs every portal's real auth flow with the
// saved demo credentials, so no login popups are needed on stage.
export async function connectAllDemo() {
  const res = await fetch(`${BACKEND_URL}/connect/demo-all`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to connect accounts");
  return res.json();
}

export async function disconnectPortal(portal) {
  const res = await fetch(`${BACKEND_URL}/connect/${portal}/disconnect`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to disconnect");
  return res.json();
}

export async function getDashboardSummary() {
  const res = await fetch(`${BACKEND_URL}/dashboard/summary`);
  if (!res.ok) throw new Error("Failed to load dashboard");
  return res.json();
}

// --- Detail endpoints (drill-down charts). Each needs a bearer token, but
// the frontend never handles tokens directly — instead we ask the backend
// for the detail data through a small per-portal proxy path that reuses the
// stored server-side token. To keep this simple and avoid duplicating auth
// logic in the browser, these call the dashboard-adjacent detail routes
// which the backend exposes without requiring the frontend to hold a token.
async function getJson(path) {
  const res = await fetch(`${BACKEND_URL}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${path}`);
  }
  return res.json();
}

export const getCashflow = () => getJson("/dashboard/detail/banking/cashflow");
export const getSpendingBreakdown = () => getJson("/dashboard/detail/creditcard/spending-breakdown");
export const getPerformance = () => getJson("/dashboard/detail/brokerage/performance");
export const getAmortization = () => getJson("/dashboard/detail/mortgage/amortization");

// --- Agentic action execution (deterministic, human-confirmed only) ---
export async function executeAction(type, amount) {
  const res = await fetch(`${BACKEND_URL}/actions/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type, amount }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Failed to execute action");
  }
  return res.json();
}

// --- Streaming chat / advice (Server-Sent Events over a POST body) ---
// EventSource doesn't support POST, so we read the stream manually and
// split on the "\n\n" SSE record separator.
async function streamPost(path, body, onEvent) {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  if (!res.ok || !res.body) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || "Request failed");
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const records = buffer.split("\n\n");
    buffer = records.pop(); // last chunk may be incomplete
    for (const record of records) {
      const line = record.split("\n").find((l) => l.startsWith("data: "));
      if (!line) continue;
      try {
        onEvent(JSON.parse(line.slice(6)));
      } catch {
        // ignore malformed lines rather than breaking the whole stream
      }
    }
  }
}

export function streamChat(message, onEvent) {
  return streamPost("/orchestrator/chat/stream", { message }, onEvent);
}

export function streamAdvice(onEvent) {
  return streamPost("/orchestrator/advice/stream", {}, onEvent);
}
