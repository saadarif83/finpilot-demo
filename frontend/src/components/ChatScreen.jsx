import { useState, useRef, useEffect } from "react";
import { streamChat } from "../api";
import ActivityFeed from "./ActivityFeed";
import ProposalCard from "./ProposalCard";

const SUGGESTED = [
  "Should I take this vacation?",
  "Should I make an extra mortgage payment to reduce my total interest?",
  "Where should my idle cash go?",
  "Should I pay down my credit card with brokerage cash?",
];

export default function ChatScreen({ onActionExecuted }) {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi, I'm FinPilot. Connect your accounts, then ask me anything about your finances." },
  ]);
  const [input, setInput] = useState("");
  const [liveSteps, setLiveSteps] = useState([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, liveSteps]);

  async function handleSend(text) {
    const messageText = text ?? input;
    if (!messageText.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", text: messageText }]);
    setInput("");
    setLoading(true);
    setLiveSteps([]);

    try {
      await streamChat(messageText, (event) => {
        if (event.type === "final") {
          setMessages((m) => [...m, { role: "assistant", text: event.reply, toolCalls: event.tool_calls, proposal: event.proposal }]);
          setLoading(false);
          setLiveSteps([]);
        } else if (event.type === "error") {
          setMessages((m) => [...m, { role: "assistant", text: `⚠️ ${event.message}`, isError: true }]);
          setLoading(false);
          setLiveSteps([]);
        } else {
          setLiveSteps((s) => [...s, event]);
        }
      });
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", text: `⚠️ ${err.message}`, isError: true }]);
      setLoading(false);
      setLiveSteps([]);
    }
  }

  return (
    <div className="chat-screen">
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role} ${m.isError ? "error" : ""}`}>
            {m.text}
            {m.proposal && <ProposalCard proposal={m.proposal} onExecuted={onActionExecuted} />}
          </div>
        ))}
        {loading && <ActivityFeed steps={liveSteps} active={true} />}
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
