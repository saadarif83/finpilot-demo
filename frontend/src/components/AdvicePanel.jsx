import { useState, useEffect, useRef } from "react";
import { streamAdvice } from "../api";
import ActivityFeed from "./ActivityFeed";
import ProposalCard from "./ProposalCard";

export default function AdvicePanel({ onClose, onActionExecuted }) {
  const [steps, setSteps] = useState([]);
  const [active, setActive] = useState(true);
  const [reply, setReply] = useState(null);
  const [proposal, setProposal] = useState(null);
  const [error, setError] = useState(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return; // guard against React StrictMode double-invoke
    started.current = true;

    streamAdvice((event) => {
      if (event.type === "final") {
        setReply(event.reply);
        setProposal(event.proposal);
        setActive(false);
      } else if (event.type === "error") {
        setError(event.message);
        setActive(false);
      } else {
        setSteps((s) => [...s, event]);
      }
    }).catch((err) => {
      setError(err.message);
      setActive(false);
    });
  }, []);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>✨ Today's advice</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <ActivityFeed steps={steps} active={active} />

        {error && <div className="detail-error">⚠️ {error}</div>}
        {reply && <div className="advice-reply">{reply}</div>}
        {proposal && <ProposalCard proposal={proposal} onExecuted={onActionExecuted} />}
      </div>
    </div>
  );
}
