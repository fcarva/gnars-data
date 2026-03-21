import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ForkRiskData } from "@/lib/gnars-data";

interface ForkRiskMonitorProps {
  data: ForkRiskData | null;
}

function riskClass(level: string): string {
  if (level === "high") return "warning";
  if (level === "medium") return "accent";
  return "success";
}

export function ForkRiskMonitor({ data }: ForkRiskMonitorProps) {
  if (!data || !data.timeseries.length) {
    return <div className="analytics-note">No fork-risk series available.</div>;
  }

  return (
    <div className="analytics-fork-wrap">
      <div className="analytics-overview-grid analytics-overview-grid-compact">
        <div className="analytics-overview-card">
          <div className="analytics-overview-label">LATEST RISK</div>
          <div className="analytics-overview-value">{data.overview.latest_risk_level.toUpperCase()}</div>
        </div>
        <div className="analytics-overview-card">
          <div className="analytics-overview-label">TOP1 SHARE</div>
          <div className="analytics-overview-value">{data.overview.latest_top1_share_pct?.toFixed(1) || "-"}%</div>
        </div>
        <div className="analytics-overview-card">
          <div className="analytics-overview-label">TOP3 SHARE</div>
          <div className="analytics-overview-value">{data.overview.latest_top3_share_pct?.toFixed(1) || "-"}%</div>
        </div>
        <div className="analytics-overview-card">
          <div className="analytics-overview-label">GINI</div>
          <div className="analytics-overview-value">{typeof data.overview.latest_gini === "number" ? data.overview.latest_gini.toFixed(3) : "-"}</div>
        </div>
      </div>

      <div className="analytics-timeseries-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data.timeseries} margin={{ top: 8, right: 20, left: 10, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" />
            <XAxis dataKey="month" tick={{ fill: "var(--muted)", fontSize: 10 }} tickLine={false} axisLine={{ stroke: "var(--line)" }} minTickGap={26} />
            <YAxis tick={{ fill: "var(--muted)", fontSize: 11 }} tickFormatter={(value) => `${value.toFixed(0)}%`} axisLine={{ stroke: "var(--line)" }} tickLine={false} width={48} domain={[0, 100]} />
            <Tooltip
              formatter={(value, key) => [`${Number(value ?? 0).toFixed(2)}%`, String(key)]}
              contentStyle={{ background: "var(--surface)", border: "1px solid var(--line)", borderRadius: "8px" }}
            />
            <Line type="monotone" dataKey="top1_share_pct" stroke="var(--accent-orange)" strokeWidth={2} dot={false} name="Top1" />
            <Line type="monotone" dataKey="top3_share_pct" stroke="var(--accent-red)" strokeWidth={2} dot={false} name="Top3" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="analytics-block-title">CONCENTRATION ALERTS</div>
      <div className="analytics-timeline-list">
        {data.alerts.length === 0 ? (
          <div className="analytics-note">No concentration alerts in tracked window.</div>
        ) : (
          data.alerts.map((alert) => (
            <div key={`${alert.month}:${alert.level}`} className="analytics-timeline-item">
              <div className="analytics-timeline-date">{alert.month}</div>
              <div className="analytics-timeline-main">{alert.message}</div>
              <div className={`badge ${riskClass(alert.level)}`}>{alert.level.toUpperCase()}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
