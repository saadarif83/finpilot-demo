import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from "recharts";
import { SPENDING_CATEGORY_COLORS, CATEGORICAL, GRIDLINE, TEXT_MUTED, CHART_SURFACE } from "../../colors";

// Horizontal bar chart rather than a pie: with 6 categories, bar length
// compares magnitude far more precisely than pie-slice angle, and each
// category keeps a fixed color regardless of month-to-month rank changes.
export default function SpendingBreakdown({ data, month }) {
  const sorted = [...data].sort((a, b) => b.amount - a.amount);
  return (
    <div className="chart-card">
      <div className="chart-title">Spending by category {month ? `— ${month}` : ""}</div>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={sorted} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRIDLINE} horizontal={false} />
          <XAxis type="number" stroke={TEXT_MUTED} fontSize={12} tickFormatter={(v) => `$${v}`} />
          <YAxis type="category" dataKey="name" stroke={TEXT_MUTED} fontSize={12} width={90} tickLine={false} />
          <Tooltip
            contentStyle={{ background: CHART_SURFACE, border: "1px solid #2a2a3a", borderRadius: 8 }}
            formatter={(value) => `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
          />
          <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
            {sorted.map((entry) => (
              <Cell key={entry.name} fill={SPENDING_CATEGORY_COLORS[entry.name] || CATEGORICAL.red} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
