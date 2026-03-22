import { useState, useEffect, useMemo } from "react";
import { FeedHeader } from "@/components/FeedHeader";
import { EventRow } from "@/components/EventRow";
import { MetricsBar } from "@/components/MetricsBar";
import { AnalyticsDashboard } from "@/components/AnalyticsDashboard";
import { VotesTable } from "@/components/VotesTable";
import { MilestonesTable } from "@/components/MilestonesTable";
import {
  fetchTimeline,
  fetchProposalVoteEvents,
  fetchTreasuryEvents,
  mergeEvents,
  fetchMetrics,
  fetchMembers,
  fetchProposalTags,
  fetchTreasury,
  fetchFundingAnalysis,
  fetchMilestonesData,
  fetchSankeyData,
  fetchEfficiencyData,
  fetchGovernanceData,
  fetchActivityTimeseriesData,
  fetchDelegationGraphData,
  fetchRunwayScenariosData,
  fetchForkRiskData,
  filterEvents,
  type TimelineEvent,
  type DaoMetrics,
  type Member,
  type ProposalTagRecord,
  type FundingAnalysis,
  type MilestoneRecord,
  type SankeyData,
  type EfficiencyData,
  type GovernanceData,
  type ActivityTimeseriesData,
  type DelegationGraphData,
  type RunwayScenariosData,
  type ForkRiskData,
  type EventFilter,
} from "@/lib/gnars-data";

const Index = () => {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [metrics, setMetrics] = useState<DaoMetrics | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [proposalTags, setProposalTags] = useState<ProposalTagRecord[]>([]);
  const [fundingAnalysis, setFundingAnalysis] = useState<FundingAnalysis | null>(null);
  const [milestoneRecords, setMilestoneRecords] = useState<MilestoneRecord[]>([]);
  const [sankeyData, setSankeyData] = useState<SankeyData | null>(null);
  const [efficiencyData, setEfficiencyData] = useState<EfficiencyData | null>(null);
  const [governanceData, setGovernanceData] = useState<GovernanceData | null>(null);
  const [activityData, setActivityData] = useState<ActivityTimeseriesData | null>(null);
  const [delegationGraphData, setDelegationGraphData] = useState<DelegationGraphData | null>(null);
  const [runwayScenariosData, setRunwayScenariosData] = useState<RunwayScenariosData | null>(null);
  const [forkRiskData, setForkRiskData] = useState<ForkRiskData | null>(null);
  const [treasuryUsd, setTreasuryUsd] = useState<number | null>(null);
  const [filter, setFilter] = useState<EventFilter>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      Promise.all([fetchTimeline(), fetchProposalVoteEvents(), fetchTreasuryEvents()]).then(([timeline, votes, treasuryEvents]) =>
        setEvents(mergeEvents(timeline, votes, treasuryEvents))
      ),
      fetchMetrics().then(setMetrics),
      fetchMembers().then(setMembers),
      fetchProposalTags().then(setProposalTags),
      fetchFundingAnalysis().then(setFundingAnalysis),
      fetchMilestonesData().then((payload) => setMilestoneRecords(payload.records)).catch(() => setMilestoneRecords([])),
      fetchSankeyData().then(setSankeyData),
      fetchEfficiencyData().then(setEfficiencyData),
      fetchGovernanceData().then(setGovernanceData),
      fetchActivityTimeseriesData().then(setActivityData),
      fetchDelegationGraphData().then(setDelegationGraphData),
      fetchRunwayScenariosData().then(setRunwayScenariosData),
      fetchForkRiskData().then(setForkRiskData),
      fetchTreasury().then((t) => setTreasuryUsd(t.overview.treasury_page_total_value_usd)),
    ]).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => filterEvents(events, filter), [events, filter]);
  const showAnalytics = filter === "analytics";
  const showVotesTable = filter === "votes";
  const showMilestonesTable = filter === "milestones" || filter === "deliveries";
  const shownMilestones = useMemo(() => {
    if (filter === "deliveries") {
      return milestoneRecords.filter((record) => {
        const status = (record.status || "").toLowerCase();
        return status === "completed";
      });
    }
    return milestoneRecords;
  }, [filter, milestoneRecords]);

  return (
    <div className="feed-page">
      <FeedHeader activeFilter={filter} onFilterChange={setFilter} />
      {!showAnalytics && <MetricsBar metrics={metrics} treasuryUsd={treasuryUsd} />}

      <main className="feed-main">
        {showAnalytics ? (
          metrics ? (
            <AnalyticsDashboard
              metrics={metrics}
              funding={fundingAnalysis}
              members={members}
              proposalTags={proposalTags}
              sankey={sankeyData}
              efficiency={efficiencyData}
              governance={governanceData}
              activity={activityData}
              delegationGraph={delegationGraphData}
              runwayScenarios={runwayScenariosData}
              forkRisk={forkRiskData}
            />
          ) : (
            <div className="feed-empty">Loading analytics...</div>
          )
        ) : showVotesTable ? (
          filtered.length === 0 ? (
            <div className="feed-empty">No vote records found.</div>
          ) : (
            <VotesTable events={filtered} funding={fundingAnalysis} />
          )
        ) : showMilestonesTable ? (
          <MilestonesTable
            records={shownMilestones}
            title={filter === "deliveries" ? "Deliveries" : "Milestones"}
            emptyMessage={
              filter === "deliveries"
                ? "No completed milestones in /data/milestones.json yet."
                : "No milestones found in /data/milestones.json yet."
            }
          />
        ) : loading ? (
          <div className="feed-skeleton-wrap">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="feed-skeleton-row">
                <div className="feed-skeleton time" />
                <div className="feed-skeleton kind" />
                <div className="feed-skeleton text" />
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="feed-empty">No events found for this filter.</div>
        ) : (
          <div>
            {filtered.map((event) => (
              <EventRow key={event.event_id} event={event} />
            ))}
          </div>
        )}
      </main>

      <footer className="feed-footer">
        GNARS DAO · data from{" "}
        <a href="https://github.com/fcarva/gnars-data" target="_blank" rel="noopener noreferrer" className="feed-footer-link">
          gnars-data
        </a>
      </footer>
    </div>
  );
};

export default Index;
