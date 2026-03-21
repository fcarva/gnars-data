import { ResponsiveContainer, LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, ReferenceLine } from "recharts";
import type { GovernanceData } from "@/lib/gnars-data";

interface GovernanceGiniChartProps {
  data: GovernanceData | null;
}

export function GovernanceGiniChart({ data }: GovernanceGiniChartProps) {
  const points = (data?.timeseries || []).filter((row) => typeof row.voting_power_gini === "number");
  
  const validGinis = points.map(p => p.voting_power_gini as number);
  const minGini = validGinis.length > 0 ? Math.min(...validGinis) : 0;
  const maxGini = validGinis.length > 0 ? Math.max(...validGinis) : 1;
  // Dynamic domain bounded between 0 and 1, padded for visibility
  const yDomain = [
    Math.max(0, Math.floor((minGini - 0.05) * 100) / 100),
    Math.min(1, Math.ceil((maxGini + 0.05) * 100) / 100)
  ];

  if (!points.length) {
    return <div className="analytics-note">No governance concentration timeseries available.</div>;
  }

  return (
    <div>
      <div className="analytics-block-title">VOTING POWER GINI (MONTHLY)</div>
      <div className="analytics-timeseries-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(64, 62, 60, 0.3)" />
            <XAxis dataKey="month" tick={{ fill: "#878580", fontSize: 11 }} />
            <YAxis domain={yDomain} tick={{ fill: "#878580", fontSize: 11 }} />
            <ReferenceLine y={0.55} stroke="rgba(173, 131, 1, 0.8)" strokeDasharray="4 3" label={{ value: "alert 0.55", fill: "#878580", fontSize: 10 }} />
            <Tooltip
              formatter={(value) => {
                const n = typeof value === "number" ? value : Number(value ?? 0);
                return [n.toFixed(3), "voting_power_gini"];
              }}
              contentStyle={{
                border: "1px solid rgba(64, 62, 60, 0.8)",
                borderRadius: 8,
                background: "rgba(16, 15, 15, 0.95)",
                color: "#cecdc3",
              }}
            />
            <Line type="monotone" dataKey="voting_power_gini" stroke="#205ea6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
