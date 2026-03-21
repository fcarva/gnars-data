const BASE_URL = "/data";

export interface TimelineEvent {
  event_id: string;
  date: string;
  title: string;
  summary: string;
  kind: string;
  status: string;
  project_id: string | null;
  project_name: string | null;
  archive_id: string | null;
  proposal_number: number | null;
  people_addresses: string[];
  proposal_ids: string[];
  links: string[];
  source: string;
  thumbnail_url?: string;
}

interface ProposalArchiveRecord {
  archive_id: string;
  proposal_number: number | null;
  title: string;
  status: string;
  created_at: string;
  votes: Array<{ voter?: string | null }>;
  scores_total?: number | null;
  links?: {
    source_url?: string;
    canonical_url?: string;
  };
}

interface SpendLedgerRecord {
  ledger_id: string;
  archive_id: string;
  proposal_number: number | null;
  title: string;
  status: string;
  proposal_executed_at: string | null;
  valuation_reference_at: string | null;
  asset_symbol: string;
  amount: number;
  usd_value_at_execution: number | null;
  recipient_address: string;
  proposer: string;
  source_url: string;
  canonical_url: string;
}

export interface LeaderboardEntry {
  display_name: string;
  address: string;
  slug: string;
  value: number;
  label: string;
}

export interface DaoMetrics {
  overview: {
    proposal_count: number;
    active_proposal_count: number;
    successful_proposal_count: number;
    proposal_success_rate_pct: number;
    people_count: number;
    holders_count: number;
    delegates_count: number;
    contributors_count: number;
    unique_voters_count: number;
    avg_votes_per_proposal: number;
    treasury_assets_count: number;
    treasury_total_value_usd: number;
    outflows_eth: number;
    outflows_usdc: number;
    proposal_status_counts: Record<string, number>;
    proposal_category_counts: Record<string, number>;
  };
  treasury: {
    wallet_address: string;
    treasury_page_total_value_usd: number;
    assets: { symbol: string; name: string; amount: number; value_usd: number }[];
  };
  leaderboards: {
    eth_received: LeaderboardEntry[];
    usdc_received: LeaderboardEntry[];
    proposal_count: LeaderboardEntry[];
    attendance_pct: LeaderboardEntry[];
    active_votes: LeaderboardEntry[];
  };
}

export interface Member {
  member_id: string;
  display_name: string;
  address: string;
  role: string;
  status: string;
  domains: string[];
  links: Record<string, string | null>;
  metrics: {
    token_count: number;
    active_votes: number;
    votes_count: number;
    attendance_pct: number;
    like_pct: number;
  };
  notes: string;
}

export interface TreasuryAsset {
  asset_id: string;
  asset_type: string;
  symbol: string;
  name: string;
  amount: number;
  value_usd: number;
}

export interface FundingProposalStage {
  stage: string;
  platform: string;
  proposal_ref: string;
  proposed_at: string | null;
  status: string | null;
  url: string;
  summary: string;
  governance: {
    for_votes: number | null;
    against_votes: number | null;
    abstain_votes: number | null;
    quorum: number | null;
  };
}

export interface FundingSource {
  funding_source_id: string;
  title: string;
  status: string;
  source_date: string | null;
  requested_amount: {
    currency: string;
    amount: number;
    usd_estimate_hint?: number | null;
  };
  usd_estimate_at_source: number | null;
  usd_estimate_fx: string | null;
  proposal_chain: FundingProposalStage[];
}

export interface FundingAllocation {
  archive_id: string;
  proposal_number: number | null;
  title: string;
  status: string;
  chain: string;
  created_at: string;
  executed_spend_usd: number;
  vote_count: number;
  voting_power: number;
  cost_per_vote_usd: number | null;
  cost_per_voting_power_usd: number | null;
  source_url: string;
}

export interface FundingTimeseriesPoint {
  month: string;
  executed_spend_usd: number;
  proposal_count: number;
  vote_count: number;
  voting_power: number;
  cost_per_vote_usd: number | null;
  cost_per_voting_power_usd: number | null;
}

export interface FundingAnalysis {
  dataset: "funding_analysis";
  as_of: string;
  version: number;
  summary: {
    funding_sources: number;
    approved_funding_usd_estimate: number;
    potential_funding_usd_estimate: number;
    executed_spend_usd: number;
    coverage_ratio_approved: number | null;
    coverage_ratio_potential: number | null;
  };
  funding_sources: FundingSource[];
  allocation_by_proposal: FundingAllocation[];
  voting_power_timeseries: FundingTimeseriesPoint[];
  method_notes: string[];
  context_sources: string[];
  warnings: string[];
}

export interface SankeyNode {
  id: number;
  label: string;
}

export interface SankeyLink {
  source: number;
  target: number;
  value: number;
}

export interface SankeyData {
  dataset: "sankey";
  as_of: string;
  version: number;
  track: string;
  nodes: SankeyNode[];
  links: SankeyLink[];
  decoding?: {
    matched_routes: number;
    unmatched_routes: number;
    selector_reference: Record<string, string>;
  };
}

export interface EfficiencyTimeseriesPoint {
  month: string;
  proposal_count: number;
  executed_spend_usd: number;
  cost_per_vote_usd: number | null;
  cost_per_voting_power_usd: number | null;
  spend_velocity_usd: number;
}

export interface EfficiencyData {
  dataset: "efficiency";
  as_of: string;
  version: number;
  allocation_by_proposal: FundingAllocation[];
  timeseries: EfficiencyTimeseriesPoint[];
}

export interface GovernanceTimeseriesPoint {
  month: string;
  proposal_count: number;
  unique_voters: number;
  turnout_pct: number | null;
  voting_power_gini: number | null;
}

export interface GovernanceData {
  dataset: "governance";
  as_of: string;
  version: number;
  overview: {
    holders_count: number;
    proposals_total: number;
    active_proposals: number;
    proposal_success_rate_pct: number;
    unique_voters_total: number;
  };
  timeseries: GovernanceTimeseriesPoint[];
}

export interface GrowthTimeseriesPoint {
  month: string;
  active_voters: number;
  new_voters: number;
  retained_voters: number;
  retention_pct: number | null;
  unique_proposers: number;
}

export interface GrowthCohortPoint {
  cohort_month: string;
  cohort_size: number;
  m_plus_1: number | null;
  m_plus_3: number | null;
  m_plus_6: number | null;
  m_plus_12: number | null;
}

export interface GrowthData {
  dataset: "growth";
  as_of: string;
  version: number;
  overview: {
    holders_count: number;
    unique_voters_total: number;
    active_voter_pct: number | null;
    proposers_total: number;
  };
  timeseries: GrowthTimeseriesPoint[];
  cohort_retention?: GrowthCohortPoint[];
}

export interface ActivityTimeseriesRecord {
  date: string;
  proposals_created: number;
  proposals_closed: number;
  proposals_executed: number;
  proposals_defeated: number;
  proposals_cancelled: number;
  proposals_active: number;
  payouts_count: number;
  payouts_eth: number;
  payouts_usdc: number;
  payouts_gnars: number;
  updates_count: number;
  deliveries_count: number;
}

export interface ActivityTimeseriesData {
  dataset: "activity_timeseries";
  as_of: string;
  version: number;
  granularity: "day" | "week" | "month";
  records: ActivityTimeseriesRecord[];
}

export interface DelegationGraphNode {
  id: string;
  label: string;
  x: number;
  y: number;
  total_votes: number;
  vote_events: number;
  degree: number;
  betweenness: number;
}

export interface DelegationGraphLink {
  source: string;
  target: string;
  weight: number;
  co_votes: number;
}

export interface DelegationGraphData {
  dataset: "delegation_graph";
  as_of: string;
  version: number;
  overview: {
    node_count: number;
    edge_count: number;
    density: number;
    largest_component_size: number;
  };
  nodes: DelegationGraphNode[];
  links: DelegationGraphLink[];
}

export interface RunwayProjectionPoint {
  month: string;
  balance_usd: number;
}

export interface RunwayScenario {
  scenario_id: string;
  label: string;
  monthly_burn_usd: number;
  monthly_inflow_usd: number;
  runway_months: number;
  projection: RunwayProjectionPoint[];
}

export interface RunwayScenariosData {
  dataset: "runway_scenarios";
  as_of: string;
  version: number;
  overview: {
    treasury_balance_usd: number;
    baseline_monthly_burn_usd: number;
    observation_months: string[];
  };
  scenarios: RunwayScenario[];
}

export interface ForkRiskPoint {
  month: string;
  voter_count: number;
  top1_share_pct: number;
  top3_share_pct: number;
  top5_share_pct: number;
  hhi: number;
  gini: number | null;
  risk_level: "low" | "medium" | "high";
}

export interface ForkRiskAlert {
  month: string;
  level: "medium" | "high";
  message: string;
}

export interface ForkRiskData {
  dataset: "fork_risk";
  as_of: string;
  version: number;
  overview: {
    latest_month: string | null;
    latest_risk_level: "low" | "medium" | "high" | "unknown";
    latest_top1_share_pct: number | null;
    latest_top3_share_pct: number | null;
    latest_gini: number | null;
  };
  timeseries: ForkRiskPoint[];
  alerts: ForkRiskAlert[];
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}/${path}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch ${path}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchTimeline(): Promise<TimelineEvent[]> {
  const data = await fetchJson<{ records: TimelineEvent[] }>("timeline_events.json");
  return data.records;
}

export async function fetchProposalVoteEvents(): Promise<TimelineEvent[]> {
  const data = await fetchJson<{ records: ProposalArchiveRecord[] }>("proposals_archive.json");
  return data.records
    .filter((record) => (record.votes?.length || 0) > 0)
    .map((record) => {
      const voters = (record.votes || [])
        .map((vote) => (vote.voter || "").toLowerCase())
        .filter((value): value is string => value.startsWith("0x"));
      const uniqueVoters = Array.from(new Set(voters));
      return {
        event_id: `vote:${record.archive_id}`,
        date: record.created_at,
        title: `Vote activity on proposal #${record.proposal_number ?? "?"}`,
        summary: `${record.votes.length} votes recorded · voting power ${Math.round(record.scores_total || 0).toLocaleString()}`,
        kind: "vote",
        status: record.status,
        project_id: null,
        project_name: null,
        archive_id: record.archive_id,
        proposal_number: record.proposal_number,
        people_addresses: uniqueVoters,
        proposal_ids: [record.archive_id],
        links: [record.links?.canonical_url || record.links?.source_url || ""].filter(Boolean),
        source: "proposals_archive",
        thumbnail_url: undefined,
      };
    });
}

export async function fetchTreasuryEvents(): Promise<TimelineEvent[]> {
  const data = await fetchJson<{ records: SpendLedgerRecord[] }>("spend_ledger.json");
  return data.records.map((record) => {
    const date = record.proposal_executed_at || record.valuation_reference_at || new Date().toISOString();
    const usd = typeof record.usd_value_at_execution === "number" ? `$${record.usd_value_at_execution.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "n/a";
    return {
      event_id: `treasury:${record.ledger_id}`,
      date,
      title: `Treasury payout on proposal #${record.proposal_number ?? "?"}`,
      summary: `${record.amount.toLocaleString(undefined, { maximumFractionDigits: 4 })} ${record.asset_symbol} · ${usd}`,
      kind: "treasury",
      status: record.status,
      project_id: null,
      project_name: null,
      archive_id: record.archive_id,
      proposal_number: record.proposal_number,
      people_addresses: [record.proposer, record.recipient_address].filter(Boolean),
      proposal_ids: [record.archive_id],
      links: [record.canonical_url || record.source_url].filter(Boolean),
      source: "spend_ledger",
      thumbnail_url: undefined,
    };
  });
}

export function mergeEvents(...groups: TimelineEvent[][]): TimelineEvent[] {
  const byId = new Map<string, TimelineEvent>();
  for (const group of groups) {
    for (const event of group) {
      if (!byId.has(event.event_id)) {
        byId.set(event.event_id, event);
      }
    }
  }
  return Array.from(byId.values()).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
}

export async function fetchMetrics(): Promise<DaoMetrics> {
  const data = await fetchJson<DaoMetrics>("dao_metrics.json");
  return data;
}

export async function fetchMembers(): Promise<Member[]> {
  const data = await fetchJson<{ records: Member[] }>("members.json");
  return data.records;
}

export async function fetchTreasury(): Promise<{
  overview: { treasury_page_total_value_usd: number };
  records: TreasuryAsset[];
}> {
  const data = await fetchJson<{
    overview: { treasury_page_total_value_usd: number };
    records: TreasuryAsset[];
  }>("treasury.json");
  return data;
}

export async function fetchFundingAnalysis(): Promise<FundingAnalysis> {
  const data = await fetchJson<FundingAnalysis>("funding_analysis.json");
  return data;
}

export async function fetchSankeyData(): Promise<SankeyData> {
  const data = await fetchJson<SankeyData>("sankey.json");
  return data;
}

export async function fetchEfficiencyData(): Promise<EfficiencyData> {
  const data = await fetchJson<EfficiencyData>("efficiency.json");
  return data;
}

export async function fetchGovernanceData(): Promise<GovernanceData> {
  const data = await fetchJson<GovernanceData>("governance.json");
  return data;
}

export async function fetchGrowthData(): Promise<GrowthData> {
  const data = await fetchJson<GrowthData>("growth.json");
  return data;
}

export async function fetchActivityTimeseriesData(): Promise<ActivityTimeseriesData> {
  const data = await fetchJson<ActivityTimeseriesData>("activity_timeseries.json");
  return data;
}

export async function fetchDelegationGraphData(): Promise<DelegationGraphData> {
  const data = await fetchJson<DelegationGraphData>("delegation_graph.json");
  return data;
}

export async function fetchRunwayScenariosData(): Promise<RunwayScenariosData> {
  const data = await fetchJson<RunwayScenariosData>("runway_scenarios.json");
  return data;
}

export async function fetchForkRiskData(): Promise<ForkRiskData> {
  const data = await fetchJson<ForkRiskData>("fork_risk.json");
  return data;
}

export function relativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHr = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return "now";
  if (diffMin < 60) return `${diffMin}m`;
  if (diffHr < 24) return `${diffHr}h`;
  if (diffDay < 30) return `${diffDay}d`;
  return `${Math.floor(diffDay / 30)}mo`;
}

export function shortenAddress(addr: string): string {
  if (!addr || addr.length < 10) return addr;
  return `${addr.slice(0, 6)}..${addr.slice(-4)}`;
}

export type EventFilter =
  | "all"
  | "proposals"
  | "votes"
  | "treasury"
  | "milestones"
  | "deliveries"
  | "analytics";

export function filterEvents(events: TimelineEvent[], filter: EventFilter): TimelineEvent[] {
  if (filter === "all" || filter === "analytics") return events;

  const kindMap: Record<string, string[]> = {
    proposals: ["proposal", "planning"],
    votes: ["vote"],
    treasury: ["treasury", "transfer", "payout"],
    milestones: ["milestone"],
    deliveries: ["delivery"],
  };

  const kinds = kindMap[filter] || [];
  return events.filter((e) => kinds.includes(e.kind));
}
export interface TreasurySnapshot {
  date: string;
  total_value_usd: number;
}
export interface TreasurySnapshotsData {
  dataset: string;
  records: TreasurySnapshot[];
}
export async function getTreasurySnapshots(): Promise<TreasurySnapshotsData | null> {
  try {
    const res = await fetch(`${BASE_URL}/treasury_snapshots.json`);
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    return null;
  }
}
