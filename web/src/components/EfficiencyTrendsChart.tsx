import { ResponsiveContainer, ComposedChart, CartesianGrid, XAxis, YAxis, Tooltip, Bar, Line, Legend } from "recharts";
import type { EfficiencyData } from "@/lib/gnars-data";

interface EfficiencyTrendsChartProps {
  data: EfficiencyData | null;
}

function valueLabel(value: number | null): string {
  if (value === null || value === undefined) {
    return "-";
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function EfficiencyTrendsChart({ data }: EfficiencyTrendsChartProps) {
  const efficiency = data;
  const points = efficiency?.timeseries || [];
  if (!points.length) {
    return <div className="analytics-note">No efficiency timeseries available.</div>;
  }

  return (
    <div>
      <div className="analytics-block-title">COST VS VELOCITY (MONTHLY)</div>
      <div className="analytics-timeseries-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={points} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(64, 62, 60, 0.3)" />
            <XAxis dataKey="month" tick={{ fill: "#878580", fontSize: 11 }} />
            <YAxis yAxisId="left" tick={{ fill: "#878580", fontSize: 11 }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fill: "#878580", fontSize: 11 }} />
            <Tooltip
              formatter={(value, name) => {
                const numeric = typeof value === "number" ? value : value == null ? null : Number(value);
                if (name === "spend_velocity_usd" || name === "executed_spend_usd") {
                  return [`$${valueLabel(Number.isFinite(numeric as number) ? numeric : null)}`, String(name)];
                }
                return [valueLabel(Number.isFinite(numeric as number) ? numeric : null), String(name)];
              }}
              contentStyle={{
                border: "1px solid rgba(64, 62, 60, 0.8)",
                borderRadius: 8,
                background: "rgba(16, 15, 15, 0.95)",
                color: "#cecdc3",
              }}
            />
            <Legend />
            <Bar yAxisId="left" dataKey="spend_velocity_usd" name="spend_velocity_usd" fill="rgba(173, 131, 1, 0.5)" />
            <Line yAxisId="right" type="monotone" dataKey="cost_per_vote_usd" name="cost_per_vote_usd" stroke="#205ea6" strokeWidth={2} dot={false} />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="cost_per_voting_power_usd"
              name="cost_per_voting_power_usd"
              stroke="#66800b"
              strokeWidth={2}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
