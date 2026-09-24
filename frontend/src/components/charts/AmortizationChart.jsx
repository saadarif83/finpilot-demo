import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { AMORTIZATION_COLORS, GRIDLINE, TEXT_MUTED, CHART_SURFACE } from "../../colors";

export default function AmortizationChart({ data }) {
  return (
    <div className="chart-card">
      <div className="chart-title">Principal vs. interest paid per year</div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRIDLINE} vertical={false} />
          <XAxis dataKey="year" stroke={TEXT_MUTED} fontSize={12} tickLine={false} />
          <YAxis stroke={TEXT_MUTED} fontSize={12} tickLine={false} tickFormatter={(v) => `$${v / 1000}k`} />
          <Tooltip
            contentStyle={{ background: CHART_SURFACE, border: "1px solid #2a2a3a", borderRadius: 8 }}
            formatter={(value) => `$${value.toLocaleString()}`}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="principal" name="Principal" stackId="a" fill={AMORTIZATION_COLORS.principal} radius={[0, 0, 0, 0]} />
          <Bar dataKey="interest" name="Interest" stackId="a" fill={AMORTIZATION_COLORS.interest} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
