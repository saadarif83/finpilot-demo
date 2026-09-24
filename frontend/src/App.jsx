import { useState, useEffect, useCallback } from "react";
import ConnectScreen from "./components/ConnectScreen";
import ChatScreen from "./components/ChatScreen";
import { getConnectStatus } from "./api";
import "./App.css";

export default function App() {
  const [tab, setTab] = useState("connect");
  const [connected, setConnected] = useState([]);

  const refreshStatus = useCallback(() => {
    getConnectStatus()
      .then((data) => setConnected(data.connected))
      .catch(() => {});
  }, []);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">✈️ FinPilot</div>
        <div className="connected-count">{connected.length}/4 connected</div>
      </header>

      <main className="app-main">
        {tab === "connect" ? (
          <ConnectScreen connected={connected} onStatusRefresh={refreshStatus} />
        ) : (
          <ChatScreen />
        )}
      </main>

      <nav className="tab-bar">
        <button className={tab === "connect" ? "active" : ""} onClick={() => setTab("connect")}>
          🔗 Accounts
        </button>
        <button className={tab === "chat" ? "active" : ""} onClick={() => setTab("chat")}>
          💬 Chat
        </button>
      </nav>
    </div>
  );
}
