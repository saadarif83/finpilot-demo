import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "../api";

const SUGGESTED = [
  "Should I take this vacation?",
  "Should I make an extra mortgage payment to reduce my total interest?",
  "Where should my idle cash go?",
];

export default function ChatScreen() {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi, I'm FinPilot. Connect your accounts, then ask me anything about your finances." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text) {
    const messageText = text ?? input;
    if (!messageText.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", text: messageText }]);
    setInput("");
    setLoading(true);
    try {
      const result = await sendChatMessage(messageText);
      setMessages((m) => [...m, { role: "assistant", text: result.reply, toolCalls: result.tool_calls }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", text: `⚠️ ${err.message}`, isError: true }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-screen">
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role} ${m.isError ? "error" : ""}`}>
            {m.text}
            {m.toolCalls && m.toolCalls.length > 0 && (
              <details className="tool-trace">
                <summary>🔧 {m.toolCalls.length} tool call{m.toolCalls.length > 1 ? "s" : ""}</summary>
                {m.toolCalls.map((tc, j) => (
                  <div key={j} className="tool-call-item">
                    <code>{tc.tool}</code>
                  </div>
                ))}
              </details>
            )}
          </div>
        ))}
        {loading && <div className="bubble assistant loading">FinPilot is checking your accounts…</div>}
        <div ref={bottomRef} />
      </div>

      {messages.length <= 1 && (
        <div className="suggestions">
          {SUGGESTED.map((s) => (
            <button key={s} className="suggestion-chip" onClick={() => handleSend(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="input-bar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask FinPilot…"
        />
        <button onClick={() => handleSend()} disabled={loading}>Send</button>
      </div>
    </div>
  );
}
