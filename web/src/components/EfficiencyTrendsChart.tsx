import { useState } from "react";
import { ResponsiveContainer, ComposedChart, CartesianGrid, XAxis, YAxis, Tooltip, Bar, Line } from "recharts";
import type { EfficiencyData } from "@/lib/gnars-data";
import { fmtDate, fmtUSD } from "@/lib/format";

interface EfficiencyTrendsChartProps {
  data: EfficiencyData | null;
}

export function EfficiencyTrendsChart({ data }: EfficiencyTrendsChartProps) {
  const [filter, setFilter] = useState<"ALL" | "12M" | "6M">("ALL");
  const efficiency = data;
  const points = efficiency?.timeseries || [];
  
  if (!points.length) {
    return <div className="analytics-note">No efficiency timeseries available.</div>;
  }

  let filteredPoints = points;
  if (filter === "12M") filteredPoints = points.slice(-12);
  if (filter === "6M") filteredPoints = points.slice(-6);

  // KPIs
  const last12Props = (efficiency?.allocation_by_proposal || []).slice(-12);
  const validCostPerVote = last12Props.filter(p => typeof p.cost_per_vote_usd === "number" && p.cost_per_vote_usd !== null);
  const avgCostPerVote = validCostPerVote.length ? validCostPerVote.reduce((sum, p) => sum + (p.cost_per_vote_usd as number), 0) / validCostPerVote.length : null;

  const validCostPerVP = last12Props.filter(p => typeof p.cost_per_voting_power_usd === "number" && p.cost_per_voting_power_usd !== null);
  const avgCostPerVP = validCostPerVP.length ? validCostPerVP.reduce((sum, p) => sum + (p.cost_per_voting_power_usd as number), 0) / validCostPerVP.length : null;

  const last12Months = points.slice(-12);
  const nonZeroMonths = last12Months.filter(p => typeof p.spend_velocity_usd === "number" && p.spend_velocity_usd > 0);
  const avgMonthlySpend = nonZeroMonths.length ? nonZeroMonths.reduce((sum, p) => sum + (p.spend_velocity_usd as number), 0) / nonZeroMonths.length : null;

  const CustomBar = (props: any) => {
    const { x, y, width, height, payload } = props;
    const isZero = !payload.spend_velocity_usd || payload.spend_velocity_usd <= 0;
    if (isZero) {
      return <rect x={x} y={y > 0 ? y : 0} width={width} height={3} fill="rgba(64,62,60,0.10)" rx={2} />;
    }
    return <rect x={x} y={y} width={width} height={height} fill="rgba(64,62,60,0.28)" stroke="#403E3C" rx={2} />;
  };

  const cleanData = filteredPoints.map(p => ({
    ...p,
    spend_velocity_usd_clean: (p.spend_velocity_usd && p.spend_velocity_usd > 0) ? p.spend_velocity_usd : 0,
    cost_per_vote_usd_clean: p.cost_per_vote_usd,
    cost_per_voting_power_usd_clean: p.cost_per_voting_power_usd
  }));

  const CustomTooltipInfo = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ background: "#FFFCF0", border: "1px solid #E6E4D9", padding: "10px", borderRadius: "6px", fontSize: "12px", color: "#100F0F", boxShadow: "0 2px 4px rgba(0,0,0,0.05)" }}>
          <div style={{ marginBottom: "6px" }}><strong>{fmtDate(label)}</strong></div>
          {payload.map((p: any, i: number) => {
            if (p.value === null || p.value === undefined) return null;
            return (
              <div key={i} style={{ color: p.color !== "rgba(64,62,60,0.28)" ? p.color : "#403E3C", display: "flex", justifyContent: "space-between", gap: "12px", marginBottom: "4px" }}>
                <span>{p.name}:</span>
                <span style={{ fontWeight: 500 }}>{fmtUSD(Number(p.value))}</span>
              </div>
            );
          })}
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ background: "#FFFCF0", color: "#100F0F", padding: "20px", borderRadius: "10px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h4 style={{ margin: 0, fontSize: "14px", fontWeight: 600, letterSpacing: "0.05em", color: "#100F0F" }}>EFFICIENCY TRENDS</h4>
        <div style={{ display: "flex", gap: "8px" }}>
          <button onClick={() => setFilter("ALL")} style={{ padding: "4px 10px", fontSize: "11px", fontWeight: 500, background: filter === "ALL" ? "#403E3C" : "transparent", color: filter === "ALL" ? "#FFFCF0" : "#6F6E69", border: "1px solid #403E3C", borderRadius: "6px", cursor: "pointer", transition: "all 0.2s" }}>ALL TIME</button>
          <button onClick={() => setFilter("12M")} style={{ padding: "4px 10px", fontSize: "11px", fontWeight: 500, background: filter === "12M" ? "#403E3C" : "transparent", color: filter === "12M" ? "#FFFCF0" : "#6F6E69", border: "1px solid #403E3C", borderRadius: "6px", cursor: "pointer", transition: "all 0.2s" }}>LAST 12 MO</button>
          <button onClick={() => setFilter("6M")} style={{ padding: "4px 10px", fontSize: "11px", fontWeight: 500, background: filter === "6M" ? "#403E3C" : "transparent", color: filter === "6M" ? "#FFFCF0" : "#6F6E69", border: "1px solid #403E3C", borderRadius: "6px", cursor: "pointer", transition: "all 0.2s" }}>LAST 6 MO</button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginBottom: "28px" }}>
        <div style={{ background: "#FFFFFF", border: "1px solid #E6E4D9", padding: "16px", borderRadius: "8px", boxShadow: "0 1px 2px rgba(0,0,0,0.02)" }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#6F6E69", marginBottom: "6px", letterSpacing: "0.02em" }}>Avg Cost/Vote (last 12 props)</div>
          <div style={{ fontSize: "22px", fontWeight: 700, color: "#100F0F" }}>{fmtUSD(avgCostPerVote)}</div>
        </div>
        <div style={{ background: "#FFFFFF", border: "1px solid #E6E4D9", padding: "16px", borderRadius: "8px", boxShadow: "0 1px 2px rgba(0,0,0,0.02)" }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#6F6E69", marginBottom: "6px", letterSpacing: "0.02em" }}>Avg Cost/VP (last 12 props)</div>
          <div style={{ fontSize: "22px", fontWeight: 700, color: "#100F0F" }}>{fmtUSD(avgCostPerVP)}</div>
        </div>
        <div style={{ background: "#FFFFFF", border: "1px solid #E6E4D9", padding: "16px", borderRadius: "8px", boxShadow: "0 1px 2px rgba(0,0,0,0.02)" }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#6F6E69", marginBottom: "6px", letterSpacing: "0.02em" }}>Avg Spend/Mo (last 12mo, non-zero)</div>
          <div style={{ fontSize: "22px", fontWeight: 700, color: "#100F0F" }}>{fmtUSD(avgMonthlySpend)}</div>
        </div>
      </div>

      <div style={{ display: "grid", gap: "18px" }}>
        <div style={{ height: "110px", width: "100%" }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={cleanData} margin={{ top: 4, right: 6, left: 6, bottom: 0 }}>
              <CartesianGrid strokeDasharray="4 4" stroke="#E6E4D9" vertical={false} />
              <XAxis dataKey="month" tick={false} axisLine={false} tickLine={false} />
              <YAxis
                tick={{ fill: "#6F6E69", fontSize: 11, fontWeight: 500 }}
                tickFormatter={(v) => fmtUSD(Number(v))}
                axisLine={false}
                tickLine={false}
                width={56}
              />
              <Tooltip content={<CustomTooltipInfo />} cursor={{ fill: "rgba(64,62,60,0.04)" }} />
              <Bar name="Spend Velocity" dataKey="spend_velocity_usd_clean" shape={<CustomBar />} isAnimationActive={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div style={{ height: "150px", width: "100%" }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={cleanData} margin={{ top: 4, right: 6, left: 6, bottom: 0 }}>
              <CartesianGrid strokeDasharray="4 4" stroke="#E6E4D9" vertical={false} />
              <XAxis
                dataKey="month"
                tick={{ fill: "#6F6E69", fontSize: 11, fontWeight: 500 }}
                tickFormatter={fmtDate}
                axisLine={{ stroke: "#E6E4D9" }}
                tickLine={false}
                dy={8}
              />
              <YAxis
                tick={{ fill: "#6F6E69", fontSize: 11, fontWeight: 500 }}
                tickFormatter={(v) => fmtUSD(Number(v))}
                axisLine={false}
                tickLine={false}
                width={56}
                domain={[0, "auto"]}
              />
              <Tooltip content={<CustomTooltipInfo />} cursor={{ fill: "rgba(64,62,60,0.04)" }} />
              <Line
                name="Cost / Vote"
                type="monotone"
                dataKey="cost_per_vote_usd_clean"
                stroke="#24837B"
                strokeWidth={2.4}
                dot={false}
                connectNulls={false}
                isAnimationActive={false}
              />
              <Line
                name="Cost / Voting Power"
                type="monotone"
                dataKey="cost_per_voting_power_usd_clean"
                stroke="#DA702C"
                strokeWidth={2.2}
                strokeDasharray="5 3"
                dot={false}
                connectNulls={false}
                isAnimationActive={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
