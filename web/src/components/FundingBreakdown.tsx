import type { FundingAnalysis } from "@/lib/gnars-data";
import { fmtUSD } from "@/lib/format";

interface FundingBreakdownProps {
  funding: FundingAnalysis | null;
}

export function FundingBreakdown({ funding }: FundingBreakdownProps) {
  if (!funding?.summary) {
    return <div className="analytics-note">Funding breakdown unavailable.</div>;
  }

  const approved = funding.summary.approved_funding_usd_estimate || 0;
  const potential = funding.summary.potential_funding_usd_estimate || 0;
  const executed = funding.summary.executed_spend_usd || 0;

  const rows = [
    { key: "approved", label: "Approved Inflow", value: approved, color: "#24837B" },
    { key: "potential", label: "Potential Inflow", value: potential, color: "#205EA6" },
    { key: "executed", label: "Executed Outflow", value: executed, color: "#BC5215" },
  ];

  const maxValue = Math.max(...rows.map((row) => row.value), 1);

  return (
    <div className="analytics-bars">
      {rows.map((row) => (
        <div key={row.key}>
          <div className="analytics-bar-head">
            <span className="analytics-bar-label">{row.label}</span>
            <span className="analytics-bar-value">{fmtUSD(row.value)}</span>
          </div>
          <div className="analytics-bar-track">
            <div className="analytics-bar-fill" style={{ width: `${(row.value / maxValue) * 100}%`, background: row.color }} />
          </div>
        </div>
      ))}
    </div>
  );
}
