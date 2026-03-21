import type { DaoMetrics } from "@/lib/gnars-data";

interface ProposalStatusChartProps {
  metrics: DaoMetrics;
}

export function ProposalStatusChart({ metrics }: ProposalStatusChartProps) {
  const counts = metrics.overview.proposal_status_counts || {};
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((sum, [, value]) => sum + value, 0) || 1;

  return (
    <div>
      <h4 className="analytics-block-title">PROPOSAL STATUS</h4>
      <div className="analytics-bars">
        {entries.map(([label, value]) => {
          const pct = (value / total) * 100;
          return (
            <div key={label} className="analytics-bar-row">
              <div className="analytics-bar-head">
                <span className="analytics-bar-label">{label.toUpperCase()}</span>
                <span className="analytics-bar-value">{value}</span>
              </div>
              <div className="analytics-bar-track">
                <div className="analytics-bar-fill" style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
