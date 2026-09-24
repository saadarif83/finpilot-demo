import { useState, useEffect, useCallback } from "react";
import Dashboard from "./components/Dashboard";
import ChatScreen from "./components/ChatScreen";
import ConnectModal from "./components/ConnectModal";
import AdvicePanel from "./components/AdvicePanel";
import { getConnectStatus, getDashboardSummary } from "./api";
import "./App.css";

const PORTAL_ICONS = { banking: "🏦", mortgage: "🏠", creditcard: "💳", brokerage: "📈" };

export default function App() {
  const [tab, setTab] = useState("dashboard");
  const [connected, setConnected] = useState([]);
  const [summary, setSummary] = useState(null);
  const [showConnect, setShowConnect] = useState(false);
  const [showAdvice, setShowAdvice] = useState(false);

  const refreshAll = useCallback(() => {
    getConnectStatus()
      .then((data) => setConnected(data.connected))
      .catch(() => {});
    getDashboardSummary()
      .then(setSummary)
      .catch(() => {});
  }, []);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">✈️ FinPilot</div>
        <div className="header-right">
          <div className="connected-badges">
            {Object.entries(PORTAL_ICONS).map(([key, icon]) => (
              <span key={key} className={`badge-dot ${connected.includes(key) ? "connected" : ""}`} title={key}>
                {icon}
              </span>
            ))}
          </div>
          <button className="icon-btn" onClick={() => setShowConnect(true)} title="Manage connected accounts">⚙️</button>
        </div>
      </header>

      <main className="app-main">
        {tab === "dashboard" ? (
          <>
            <button className="advice-fab" onClick={() => setShowAdvice(true)}>
              ✨ Ask FinPilot for advice
            </button>
            <Dashboard summary={summary} onConnectClick={() => setShowConnect(true)} />
          </>
        ) : (
          <ChatScreen onActionExecuted={refreshAll} />
        )}
      </main>

      <nav className="tab-bar">
        <button className={tab === "dashboard" ? "active" : ""} onClick={() => setTab("dashboard")}>
          🏠 Overview
        </button>
        <button className={tab === "chat" ? "active" : ""} onClick={() => setTab("chat")}>
          💬 Chat
        </button>
      </nav>

      {showConnect && (
        <ConnectModal
          connected={connected}
          onStatusRefresh={refreshAll}
          onClose={() => setShowConnect(false)}
        />
      )}
      {showAdvice && (
        <AdvicePanel
          onClose={() => setShowAdvice(false)}
          onActionExecuted={refreshAll}
        />
      )}
    </div>
  );
}
