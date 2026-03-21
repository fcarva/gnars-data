import type {
  DaoMetrics,
  FundingAnalysis,
  Member,
  ProposalTagRecord,
  CommunitySignalsData,
  SankeyData,
  EfficiencyData,
  GovernanceData,
  ActivityTimeseriesData,
  DelegationGraphData,
  RunwayScenariosData,
  ForkRiskData,
} from "@/lib/gnars-data";
import { fmtUSD } from "@/lib/format";
import { ProposalStatusChart } from "@/components/ProposalStatusChart";
import { ProposalCategoryChart } from "@/components/ProposalCategoryChart";
import { TreasuryChart } from "@/components/TreasuryChart";
import { LeaderboardTable } from "@/components/LeaderboardTable";
import { AnalyticsSankey } from "@/components/AnalyticsSankey";
import { EfficiencyTrendsChart } from "@/components/EfficiencyTrendsChart";
import { GovernanceGiniChart } from "@/components/GovernanceGiniChart";
import { ActivityHeatmap } from "@/components/ActivityHeatmap";
import { DelegationForceGraph } from "@/components/DelegationForceGraph";
import { RunwayWhatIf } from "@/components/RunwayWhatIf";
import { ForkRiskMonitor } from "@/components/ForkRiskMonitor";
import { SportFundingTable } from "@/components/SportFundingTable";
import { AthletesLeaderboard } from "@/components/AthletesLeaderboard";
import { FundingBreakdown } from "@/components/FundingBreakdown";

interface AnalyticsDashboardProps {
  metrics: DaoMetrics;
  funding: FundingAnalysis | null;
  members: Member[];
  proposalTags: ProposalTagRecord[];
  communitySignals: CommunitySignalsData | null;
  sankey: SankeyData | null;
  efficiency: EfficiencyData | null;
  governance: GovernanceData | null;
  activity: ActivityTimeseriesData | null;
  delegationGraph: DelegationGraphData | null;
  runwayScenarios: RunwayScenariosData | null;
  forkRisk: ForkRiskData | null;
}

function fmtPct(value: number | null | undefined): string {
  if (typeof value !== "number") return "-";
  return `${(value * 100).toFixed(1)}%`;
}

export function AnalyticsDashboard({
  metrics,
  funding,
  members,
  proposalTags,
  communitySignals,
  sankey,
  efficiency,
  governance,
  activity,
  delegationGraph,
  runwayScenarios,
  forkRisk,
}: AnalyticsDashboardProps) {
  const o = metrics.overview;
  const lb = metrics.leaderboards;

  const overviewStats = [
    { label: "PROPOSALS", value: o.proposal_count.toString() },
    { label: "ACTIVE", value: o.active_proposal_count.toString() },
    { label: "SUCCESS RATE", value: `${o.proposal_success_rate_pct}%` },
    { label: "HOLDERS", value: o.holders_count.toLocaleString() },
    { label: "DELEGATES", value: o.delegates_count.toLocaleString() },
    { label: "VOTERS", value: o.unique_voters_count.toLocaleString() },
    { label: "CONTRIBUTORS", value: o.contributors_count?.toString() || "-" },
    { label: "AVG VOTES/PROP", value: o.avg_votes_per_proposal.toFixed(1) },
  ];

  const summary = funding?.summary;
  const timelineStages = (funding?.funding_sources || [])
    .flatMap((source) =>
      source.proposal_chain.map((stage) => ({
        sourceTitle: source.title,
        requested: `${source.requested_amount.amount.toLocaleString()} ${source.requested_amount.currency}`,
        ...stage,
      }))
    )
    .sort((left, right) => {
      const l = left.proposed_at ? new Date(left.proposed_at).getTime() : Number.MAX_SAFE_INTEGER;
      const r = right.proposed_at ? new Date(right.proposed_at).getTime() : Number.MAX_SAFE_INTEGER;
      return l - r;
    });

  const topAllocations = [...(funding?.allocation_by_proposal || [])]
    .sort((left, right) => right.executed_spend_usd - left.executed_spend_usd)
    .slice(0, 4);

  const latestEfficiency = funding?.voting_power_timeseries?.at(-1);
  const meanCostPerVote = (() => {
    const rows = (funding?.allocation_by_proposal || []).filter((row) => typeof row.cost_per_vote_usd === "number");
    if (!rows.length) return null;
    const total = rows.reduce((sum, row) => sum + (row.cost_per_vote_usd || 0), 0);
    return total / rows.length;
  })();

  return (
    <div className="analytics-dashboard">
      <div>
        <h3 className="analytics-section-title">OVERVIEW</h3>
        <div className="analytics-overview-grid">
          {overviewStats.map((s) => (
            <div key={s.label} className="analytics-overview-card">
              <div className="analytics-overview-label">{s.label}</div>
              <div className="analytics-overview-value">{s.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="analytics-charts-grid">
        <div className="analytics-panel">
          <ProposalStatusChart metrics={metrics} />
        </div>
        <div className="analytics-panel">
          <ProposalCategoryChart metrics={metrics} />
        </div>
        <div className="analytics-panel">
          <TreasuryChart projectedZeroDate={metrics.projected_zero_date} />
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">FUNDING TIMELINE</h3>
        <div className="analytics-panel">
          {timelineStages.length === 0 ? (
            <div className="analytics-note">No funding timeline entries found.</div>
          ) : (
            <div className="analytics-timeline-list">
              {timelineStages.map((stage) => (
                <a key={`${stage.platform}:${stage.proposal_ref}:${stage.stage}`} className="analytics-timeline-item" href={stage.url} target="_blank" rel="noopener noreferrer">
                  <div className="analytics-timeline-date">{stage.proposed_at || "unknown"}</div>
                  <div className="analytics-timeline-main">
                    <div className="analytics-timeline-title">{stage.sourceTitle} · {stage.platform} #{stage.proposal_ref}</div>
                    <div className="analytics-timeline-meta">{stage.stage.toUpperCase()} · {stage.status || "unknown"} · ask {stage.requested}</div>
                  </div>
                  <div className="analytics-timeline-votes">
                    {stage.governance.for_votes ?? "-"}/{stage.governance.against_votes ?? "-"}/{stage.governance.abstain_votes ?? "-"}
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">ALLOCATION VS CAPACITY</h3>
        <div className="analytics-overview-grid analytics-overview-grid-compact">
          <div className="analytics-overview-card">
            <div className="analytics-overview-label">APPROVED CAPACITY</div>
            <div className="analytics-overview-value">{fmtUSD(summary?.approved_funding_usd_estimate ?? null)}</div>
          </div>
          <div className="analytics-overview-card">
            <div className="analytics-overview-label">POTENTIAL CAPACITY</div>
            <div className="analytics-overview-value">{fmtUSD(summary?.potential_funding_usd_estimate ?? null)}</div>
          </div>
          <div className="analytics-overview-card">
            <div className="analytics-overview-label">EXECUTED SPEND</div>
            <div className="analytics-overview-value">{fmtUSD(summary?.executed_spend_usd ?? null)}</div>
          </div>
          <div className="analytics-overview-card">
            <div className="analytics-overview-label">POTENTIAL COVERAGE USED</div>
            <div className="analytics-overview-value">{fmtPct(summary?.coverage_ratio_potential)}</div>
          </div>
        </div>
        <div className="analytics-panel">
          <div className="analytics-block-title">TOP ALLOCATIONS</div>
          <div className="analytics-timeline-list">
            {topAllocations.map((row) => (
              <a key={row.archive_id} className="analytics-timeline-item" href={row.source_url} target="_blank" rel="noopener noreferrer">
                <div className="analytics-timeline-date">#{row.proposal_number ?? "?"}</div>
                <div className="analytics-timeline-main">
                  <div className="analytics-timeline-title">{row.title}</div>
                  <div className="analytics-timeline-meta">{row.chain.toUpperCase()} · {row.status}</div>
                </div>
                  <div className="analytics-timeline-votes">{fmtUSD(row.executed_spend_usd)}</div>
              </a>
            ))}
          </div>
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">FUNDING BREAKDOWN</h3>
        <div className="analytics-panel">
          <FundingBreakdown funding={funding} />
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">GOVERNANCE EFFICIENCY</h3>
        <div className="analytics-overview-grid analytics-overview-grid-compact">
          <div className="analytics-overview-card">
            <div className="analytics-overview-label">MEAN COST / VOTE</div>
            <div className="analytics-overview-value">{fmtUSD(meanCostPerVote)}</div>
          </div>
          <div className="analytics-overview-card">
            <div className="analytics-overview-label">LATEST MONTH</div>
            <div className="analytics-overview-value">{latestEfficiency?.month || "-"}</div>
          </div>
          <div className="analytics-overview-card">
            <div className="analytics-overview-label">LATEST COST / VOTE</div>
            <div className="analytics-overview-value">{fmtUSD(latestEfficiency?.cost_per_vote_usd ?? null)}</div>
          </div>
          <div className="analytics-overview-card">
            <div className="analytics-overview-label">LATEST COST / VOTING POWER</div>
            <div className="analytics-overview-value">
              {typeof latestEfficiency?.cost_per_voting_power_usd === "number"
                ? `$${latestEfficiency.cost_per_voting_power_usd.toFixed(4)}`
                : "-"}
            </div>
          </div>
        </div>
        <div className="analytics-panel">
          <div className="analytics-block-title">EFFICIENCY TRENDS</div>
          <EfficiencyTrendsChart data={efficiency} funding={funding} proposalTags={proposalTags} />
        </div>
        <div className="analytics-panel">
          <div className="analytics-block-title">QUALITATIVE NOTES</div>
          <ul className="analytics-notes-list">
            {(communitySignals?.field_notes || []).map((note) => (
              <li key={note.note_id}><strong>{note.title}</strong> {note.summary}</li>
            ))}
            {!communitySignals?.field_notes?.length ? <li>Loading field notes from live analytics signals...</li> : null}
          </ul>
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">GOVERNANCE CONCENTRATION</h3>
        <div className="analytics-panel">
          <GovernanceGiniChart data={governance} />
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">ACTIVITY</h3>
        <div className="analytics-panel">
          <ActivityHeatmap data={activity} />
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">DELEGATION GRAPH</h3>
        <div className="analytics-panel">
          <DelegationForceGraph data={delegationGraph} />
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">RUNWAY WHAT-IF</h3>
        <div className="analytics-panel">
          <RunwayWhatIf metrics={metrics} />
        </div>
      </div>

      <div>

        <div className="analytics-panel">
          <AnalyticsSankey data={sankey} />
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">ATHLETE FUNDING</h3>
        <div className="analytics-panel">
          <SportFundingTable />
        </div>
        <div className="analytics-panel" style={{ marginTop: 12 }}>
          <AthletesLeaderboard members={members} />
        </div>
      </div>

      <div>
        <h3 className="analytics-section-title">LEADERBOARDS</h3>
        <div className="analytics-leaderboards-grid">
          <div className="analytics-panel">
            <LeaderboardTable title="TOP ETH RECIPIENTS" entries={lb.eth_received} formatValue={(v) => `${v.toFixed(2)} ETH`} />
          </div>
          <div className="analytics-panel">
            <LeaderboardTable title="TOP USDC RECIPIENTS" entries={lb.usdc_received} formatValue={(v) => `$${v.toLocaleString()}`} />
          </div>
          <div className="analytics-panel">
            <LeaderboardTable title="TOP PROPOSERS" entries={lb.proposal_count} />
          </div>
          <div className="analytics-panel">
            <LeaderboardTable title="ATTENDANCE %" entries={lb.attendance_pct} formatValue={(v) => `${v}%`} />
          </div>
          <div className="analytics-panel">
            <LeaderboardTable title="ACTIVE VOTES" entries={lb.active_votes} />
          </div>
        </div>
      </div>
    </div>
  );
}
