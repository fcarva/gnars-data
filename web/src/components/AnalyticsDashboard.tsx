import type {
  DaoMetrics,
  FundingAnalysis,
  Member,
  ProposalTagRecord,
  SankeyData,
  EfficiencyData,
  GovernanceData,
  ActivityTimeseriesData,
  DelegationGraphData,
  RunwayScenariosData,
  ForkRiskData,
} from "@/lib/gnars-data";
import { TreasuryChart } from "@/components/TreasuryChart";
import { ProposalCategoryChart } from "@/components/ProposalCategoryChart";
import { AnalyticsSankey } from "@/components/AnalyticsSankey";
import { AthletesLeaderboard } from "@/components/AthletesLeaderboard";
import { FundingBreakdown } from "@/components/FundingBreakdown";

interface AnalyticsDashboardProps {
  metrics: DaoMetrics;
  funding: FundingAnalysis | null;
  members: Member[];
  proposalTags: ProposalTagRecord[];
  sankey: SankeyData | null;
  efficiency: EfficiencyData | null;
  governance: GovernanceData | null;
  activity: ActivityTimeseriesData | null;
  delegationGraph: DelegationGraphData | null;
  runwayScenarios: RunwayScenariosData | null;
  forkRisk: ForkRiskData | null;
}

function fmtCompactUsd(value: number | null | undefined): string {
  if (typeof value !== "number") return "-";
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}m`;
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}k`;
  return `$${Math.round(value)}`;
}

export function AnalyticsDashboard({
  metrics,
  funding,
  members,
  proposalTags,
  sankey,
  efficiency,
  governance,
  activity,
  delegationGraph,
  runwayScenarios,
  forkRisk,
}: AnalyticsDashboardProps) {
  const o = metrics.overview;
  const summary = funding?.summary;
  const tagByArchive = new Map(proposalTags.map((row) => [row.archive_id, row.semantic_category || row.primary_category || "other"]));
  const athleteSpend = (funding?.allocation_by_proposal || []).reduce((sum, row) => {
    const category = tagByArchive.get(row.archive_id);
    if (category === "athletes_riders") return sum + (row.executed_spend_usd || 0);
    return sum;
  }, 0);
  const athleteShare = summary?.executed_spend_usd ? (athleteSpend / summary.executed_spend_usd) * 100 : null;

  const overviewStats = [
    {
      label: "TREASURY",
      value: fmtCompactUsd(metrics.treasury_balance_usd ?? o.treasury_total_value_usd),
      sub: metrics.projected_zero_date ? `runway until ${metrics.projected_zero_date}` : "live treasury",
    },
    {
      label: "TOTAL FUNDING IN",
      value: fmtCompactUsd(summary?.potential_funding_usd_estimate ?? null),
      sub: `${summary?.funding_sources ?? 0} sources`,
    },
    {
      label: "TOTAL SPENT",
      value: fmtCompactUsd(summary?.executed_spend_usd ?? null),
      sub: `${(funding?.allocation_by_proposal || []).length} funded proposals`,
    },
    {
      label: "TO ATHLETES",
      value: fmtCompactUsd(athleteSpend),
      sub: `${athleteShare !== null ? athleteShare.toFixed(1) : "-"}% of spend`,
    },
    {
      label: "PASS RATE",
      value: `${o.proposal_success_rate_pct}%`,
      sub: `${o.successful_proposal_count} successful`,
    },
  ];

  return (
    <div className="analytics-dashboard">
      <div>
        <h3 className="analytics-section-title">OVERVIEW</h3>
        <div className="analytics-overview-grid analytics-overview-grid-kpi">
          {overviewStats.map((s) => (
            <div key={s.label} className="analytics-overview-card">
              <div className="analytics-overview-label">{s.label}</div>
              <div className="analytics-overview-value">{s.value}</div>
              <div className="analytics-overview-sub">{s.sub}</div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">TREASURY OVER TIME</h3>
        <div className="analytics-panel">
          <TreasuryChart
            projectedZeroDate={metrics.projected_zero_date}
            funding={funding}
            proposalTags={proposalTags}
            currentTreasuryUsd={metrics.treasury_balance_usd ?? o.treasury_total_value_usd}
            treasuryEvents={metrics.treasury_events || []}
          />
        </div>
      </div>

      <div>
        <div className="analytics-split-5-5">
          <div>
            <h3 className="analytics-section-title">PROPOSAL CATEGORIES</h3>
            <div className="analytics-panel">
              <ProposalCategoryChart metrics={metrics} />
            </div>
          </div>
          <div>
            <h3 className="analytics-section-title">FUNDING & SPEND BREAKDOWN</h3>
            <div className="analytics-panel">
              <FundingBreakdown funding={funding} proposalTags={proposalTags} />
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">CAPITAL FLOW — TREASURY TO RECIPIENTS</h3>
        <div className="analytics-panel analytics-panel-sankey">
          <AnalyticsSankey data={sankey} />
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">ATHLETES & CONTRIBUTORS — LEADERBOARD</h3>
        <div className="analytics-panel">
          <AthletesLeaderboard members={members} />
        </div>
      </div>
    </div>
  );
}
