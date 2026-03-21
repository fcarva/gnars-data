import type { DaoMetrics } from "@/lib/gnars-data";

interface MetricsBarProps {
  metrics: DaoMetrics | null;
  treasuryUsd: number | null;
}

export function MetricsBar({ metrics, treasuryUsd }: MetricsBarProps) {
  if (!metrics) return null;

  const o = metrics.overview;
  const stats = [
    { label: "PROPOSALS", value: o.proposal_count },
    { label: "ACTIVE", value: o.active_proposal_count },
    { label: "HOLDERS", value: o.holders_count.toLocaleString() },
    { label: "VOTERS", value: o.unique_voters_count },
    { label: "TREASURY", value: treasuryUsd ? `$${(treasuryUsd / 1000).toFixed(1)}k` : "-" },
    { label: "SUCCESS", value: `${o.proposal_success_rate_pct}%` },
  ];

  return (
    <div className="metrics-bar">
      <div className="metrics-bar-inner">
        {stats.map((s) => (
          <div key={s.label} className="metrics-item">
            <div className="metrics-item-label">{s.label}</div>
            <div className="metrics-item-value">{s.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
