import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { SEQUENTIAL_BLUE, GRIDLINE, TEXT_MUTED, CHART_SURFACE } from "../../colors";

// Single series (total portfolio value over time) — sequential blue, no
// legend needed since the chart title already names the one series.
export default function PerformanceChart({ data }) {
  return (
    <div className="chart-card">
      <div className="chart-title">Portfolio value over time</div>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRIDLINE} vertical={false} />
          <XAxis dataKey="month" stroke={TEXT_MUTED} fontSize={12} tickLine={false} />
          <YAxis stroke={TEXT_MUTED} fontSize={12} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} domain={["dataMin - 500", "dataMax + 500"]} />
          <Tooltip
            contentStyle={{ background: CHART_SURFACE, border: "1px solid #2a2a3a", borderRadius: 8 }}
            formatter={(value) => `$${value.toLocaleString()}`}
          />
          <Line type="monotone" dataKey="value" stroke={SEQUENTIAL_BLUE} strokeWidth={2} dot={{ r: 4, fill: SEQUENTIAL_BLUE }} activeDot={{ r: 6 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
