import type { FundingAnalysis, ProposalTagRecord } from "@/lib/gnars-data";
import { fmtUSD } from "@/lib/format";

interface FundingBreakdownProps {
  funding: FundingAnalysis | null;
  proposalTags: ProposalTagRecord[];
}

export function FundingBreakdown({ funding, proposalTags }: FundingBreakdownProps) {
  if (!funding?.summary) {
    return <div className="analytics-note">Funding breakdown unavailable.</div>;
  }

  const fundingIn = funding.summary.potential_funding_usd_estimate || 0;
  const spendOut = funding.summary.executed_spend_usd || 0;

  const inflowRows = (funding.funding_sources || [])
    .map((source) => ({
      key: source.funding_source_id,
      label: source.title,
      value: source.usd_estimate_at_source || source.requested_amount.usd_estimate_hint || 0,
      color: "#879A39",
    }))
    .filter((row) => row.value > 0)
    .sort((a, b) => b.value - a.value)
    .slice(0, 4);

  const tagByArchive = new Map(proposalTags.map((row) => [row.archive_id, row.semantic_category || row.primary_category || "other"]));
  const spendTotals = new Map<string, number>();
  for (const row of funding.allocation_by_proposal || []) {
    const category = tagByArchive.get(row.archive_id) || "other";
    let key = "Other";
    if (category === "athletes_riders") key = "Athletes";
    else if (category === "workstream_media") key = "Media";
    else if (category === "workstream_ops") key = "Operations";
    else if (category === "workstream_products" || category === "workstream_dev" || category === "irl_events") key = "Dev + Events";
    spendTotals.set(key, (spendTotals.get(key) || 0) + (row.executed_spend_usd || 0));
  }

  const spendRows = Array.from(spendTotals.entries())
    .map(([label, value]) => ({
      key: label,
      label,
      value,
      color:
        label === "Athletes" ? "#3AA99F" :
        label === "Media" ? "#8B7EC8" :
        label === "Operations" ? "#DA702C" :
        label === "Dev + Events" ? "#4385BE" : "#6F6E69",
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 4);

  const maxIn = Math.max(1, ...inflowRows.map((row) => row.value));
  const maxOut = Math.max(1, ...spendRows.map((row) => row.value));
  const utilizationPct = fundingIn > 0 ? (spendOut / fundingIn) * 100 : 0;
  const latestEfficiency = funding.voting_power_timeseries?.at(-1);
  const meanCostPerVote = (() => {
    const rows = (funding.allocation_by_proposal || []).filter((row) => typeof row.cost_per_vote_usd === "number");
    if (!rows.length) return null;
    const total = rows.reduce((sum, row) => sum + (row.cost_per_vote_usd || 0), 0);
    return total / rows.length;
  })();

  return (
    <div>
      <div className="fvs">
        <div className="fvs-cell">
          <div className="fvs-label">FUNDING IN</div>
          <div className="fvs-val" style={{ color: "#66800B" }}>{fmtUSD(fundingIn)}</div>
          <div className="fvs-rows">
            {inflowRows.map((row) => (
              <div key={row.key}>
                <div className="fvs-row">
                  <span className="fvs-key">{row.label}</span>
                  <span className="fvs-num">{fmtUSD(row.value)}</span>
                </div>
                <div className="fvs-bar-wrap">
                  <div className="fvs-bar" style={{ width: `${(row.value / maxIn) * 100}%`, background: row.color }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="fvs-cell">
          <div className="fvs-label">SPEND OUT</div>
          <div className="fvs-val" style={{ color: "#D14D41" }}>{fmtUSD(spendOut)}</div>
          <div className="fvs-rows">
            {spendRows.map((row) => (
              <div key={row.key}>
                <div className="fvs-row">
                  <span className="fvs-key">{row.label}</span>
                  <span className="fvs-num">{fmtUSD(row.value)}</span>
                </div>
                <div className="fvs-bar-wrap">
                  <div className="fvs-bar" style={{ width: `${(row.value / maxOut) * 100}%`, background: row.color }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="fvs-util">
        <div className="fvs-row">
          <span className="fvs-key">Treasury utilization</span>
          <span className="fvs-num">{utilizationPct.toFixed(1)}%</span>
        </div>
        <div className="fvs-bar-wrap fvs-util-track">
          <div className="fvs-bar fvs-util-bar" style={{ width: `${Math.min(utilizationPct, 100)}%` }} />
        </div>
      </div>

      <div className="fvs-kpis">
        <div className="fvs-kpi">
          <div className="fvs-kpi-label">MEAN COST / VOTE</div>
          <div className="fvs-kpi-value">{fmtUSD(meanCostPerVote)}</div>
        </div>
        <div className="fvs-kpi">
          <div className="fvs-kpi-label">LATEST MONTH</div>
          <div className="fvs-kpi-value">{latestEfficiency?.month || "-"}</div>
        </div>
        <div className="fvs-kpi">
          <div className="fvs-kpi-label">LATEST COST / VOTE</div>
          <div className="fvs-kpi-value">{fmtUSD(latestEfficiency?.cost_per_vote_usd ?? null)}</div>
        </div>
        <div className="fvs-kpi">
          <div className="fvs-kpi-label">LATEST COST / VOTING POWER</div>
          <div className="fvs-kpi-value">{typeof latestEfficiency?.cost_per_voting_power_usd === "number" ? `$${latestEfficiency.cost_per_voting_power_usd.toFixed(4)}` : "-"}</div>
        </div>
      </div>
    </div>
  );
}
