import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { CASHFLOW_COLORS, GRIDLINE, TEXT_MUTED, CHART_SURFACE } from "../../colors";

export default function CashflowChart({ data }) {
  return (
    <div className="chart-card">
      <div className="chart-title">Money in vs. money out</div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRIDLINE} vertical={false} />
          <XAxis dataKey="month" stroke={TEXT_MUTED} fontSize={12} tickLine={false} />
          <YAxis stroke={TEXT_MUTED} fontSize={12} tickLine={false} tickFormatter={(v) => `$${v / 1000}k`} />
          <Tooltip
            contentStyle={{ background: CHART_SURFACE, border: "1px solid #2a2a3a", borderRadius: 8 }}
            formatter={(value) => `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="in" name="Money in" fill={CASHFLOW_COLORS.in} radius={[4, 4, 0, 0]} />
          <Bar dataKey="out" name="Money out" fill={CASHFLOW_COLORS.out} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
