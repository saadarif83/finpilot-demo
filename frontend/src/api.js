const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export async function getConnectStatus() {
  const res = await fetch(`${BACKEND_URL}/connect/status`);
  if (!res.ok) throw new Error("Failed to load connection status");
  return res.json();
}

export function openConnectPopup(portal) {
  // Opens the SIMULATED bank/mortgage/brokerage login screen in a popup,
  // exactly like a real OAuth "connect your account" flow would.
  const url = `${BACKEND_URL}/connect/${portal}`;
  const popup = window.open(url, "connect", "width=380,height=560");
  return popup;
}

export async function connectCreditCard() {
  // Credit card uses Client Credentials — no popup, just a direct call.
  const res = await fetch(`${BACKEND_URL}/connect/creditcard`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to connect credit card");
  return res.json();
}

export async function disconnectPortal(portal) {
  const res = await fetch(`${BACKEND_URL}/connect/${portal}/disconnect`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to disconnect");
  return res.json();
}

export async function sendChatMessage(message) {
  const res = await fetch(`${BACKEND_URL}/orchestrator/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "FinPilot ran into an error");
  }
  return res.json();
}
