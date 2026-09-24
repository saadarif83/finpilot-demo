import { useState, useEffect } from "react";
import { getCashflow, getSpendingBreakdown, getPerformance, getAmortization } from "../api";
import CashflowChart from "./charts/CashflowChart";
import SpendingBreakdown from "./charts/SpendingBreakdown";
import PerformanceChart from "./charts/PerformanceChart";
import AmortizationChart from "./charts/AmortizationChart";

const TITLES = {
  banking: "Checking & Savings",
  creditcard: "Credit Card",
  brokerage: "Brokerage",
  mortgage: "Mortgage",
};

export default function DetailView({ accountType, onClose }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const loaders = {
      banking: getCashflow,
      creditcard: getSpendingBreakdown,
      brokerage: getPerformance,
      mortgage: getAmortization,
    };
    loaders[accountType]()
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(e.message));
    return () => { cancelled = true; };
  }, [accountType]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{TITLES[accountType]}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {error && <div className="detail-error">⚠️ {error}</div>}
        {!data && !error && <div className="detail-loading">Loading…</div>}

        {data && accountType === "banking" && <CashflowChart data={data.cashflow} />}
        {data && accountType === "creditcard" && <SpendingBreakdown data={data.categories} month={data.month} />}
        {data && accountType === "brokerage" && <PerformanceChart data={data.history} />}
        {data && accountType === "mortgage" && <AmortizationChart data={data.schedule} />}
      </div>
    </div>
  );
}
