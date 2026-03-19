import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { scaleLinear } from "d3-scale";
import { curveMonotoneX, line } from "d3-shape";
import { renderPageMarkup } from "../src/entry-server";
import type {
  ActivityTimeseriesData,
  ActivityViewData,
  ActivityViewScene,
  CommunityCard,
  CommunityIndexPageProps,
  CommunityProfilePageProps,
  CommunitySignalsData,
  DaoMetrics,
  FeedStreamData,
  FilterFacetsData,
  InsightsData,
  NetworkPageProps,
  NetworkViewData,
  NotesIndexRecord,
  PagePayload,
  PersonRecord,
  ProposalEnrichedData,
  ProposalEnrichedRecord,
  ProjectCard,
  ProjectDetailPageProps,
  ProjectRollupRecord,
  ProposalArchiveRecord,
  ProposalCard,
  ProposalDetailPageProps,
  SpendLedgerRecord,
  TimelineCard,
  TimelineEventRecord,
  TreasuryFlowsData,
  TreasuryPageProps,
  TreasuryViewData,
} from "../src/types";
import {
  communityHref,
  getAthleteEconomics,
  groupAssetTotals,
  isSuccessfulProposal,
  personLabel,
  personSubtitle,
  projectBudgetAssets,
  projectHref,
  projectSpentAssets,
  proposalBudgetLabel,
  proposalHref,
  timelineHref,
  tribeLabels,
} from "../src/lib/selectors";
import { formatAmount, formatDate, primaryAssetLabel, titleCase } from "../src/lib/format";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const publicDataDir = path.join(webRoot, "public", "data");
const distDir = path.join(webRoot, "dist");

function truncate(value: string, limit = 180): string {
  const clean = value.trim();
  return clean.length > limit ? `${clean.slice(0, limit - 3)}...` : clean;
}

function uniqueBy<T>(items: T[], keyGetter: (item: T) => string): T[] {
  const seen = new Set<string>();
  const output: T[] = [];
  for (const item of items) {
    const key = keyGetter(item);
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    output.push(item);
  }
  return output;
}

function htmlEscapeJson(value: unknown): string {
  return JSON.stringify(value)
    .replace(/</g, "\\u003c")
    .replace(/\u2028/g, "\\u2028")
    .replace(/\u2029/g, "\\u2029");
}

function proposalAliases(proposal: ProposalArchiveRecord): string[] {
  const aliases = [proposal.archive_id.toLowerCase(), proposal.proposal_key.toLowerCase()];
  if (proposal.proposal_number !== null) {
    aliases.push(`${proposal.chain}-${proposal.proposal_number}`.toLowerCase());
    aliases.push(`${proposal.platform}-${proposal.chain}-${proposal.proposal_number}`.toLowerCase());
  }
  return aliases;
}

async function loadJson<T>(filename: string): Promise<T> {
  return JSON.parse(await fs.readFile(path.join(publicDataDir, filename), "utf8")) as T;
}

function buildProposalBudgetMap(spendLedger: SpendLedgerRecord[]) {
  const grouped = new Map<string, SpendLedgerRecord[]>();
  for (const record of spendLedger) {
    const records = grouped.get(record.archive_id) ?? [];
    records.push(record);
    grouped.set(record.archive_id, records);
  }
  return grouped;
}

function buildCommunityCard(
  person: PersonRecord,
  spendLedger: SpendLedgerRecord[],
  proposals: ProposalArchiveRecord[],
): CommunityCard {
  const economics = getAthleteEconomics(person.address, spendLedger, proposals, person.relationships.owned_projects);
  const tribes = tribeLabels(person.tribes?.length ? person.tribes : person.tags);
  return {
    slug: person.slug,
    href: communityHref(person.slug),
    displayName: person.display_name,
    subtitle: person.history_short || personSubtitle(person),
    tribes,
    totalReceivedLabel: economics.totalReceivedPrimary
      ? `Received ${formatAmount(economics.totalReceivedPrimary.symbol, economics.totalReceivedPrimary.amount)}`
      : "No successful treasury flows",
    approvedProposals: economics.approvedProposals,
    budgetManagedLabel: economics.budgetManagedByAsset.length
      ? `Managed ${economics.budgetManagedByAsset.map((item) => formatAmount(item.symbol, item.amount)).join(" + ")}`
      : "No approved managed budget",
    featured: person.tags.includes("athlete") || person.tags.includes("proposer") || person.tags.includes("recipient"),
    status: person.status,
    ethReceived: person.receipts.eth_received,
    usdcReceived: person.receipts.usdc_received,
    budgetManagedPrimary: economics.budgetManagedByAsset[0]?.amount ?? 0,
    proofCount: person.proof_count ?? 0,
    lastSeenAt: person.last_seen_at,
    searchText: `${person.display_name} ${person.role} ${(person.tribes || person.tags).join(" ")} ${person.headline || ""}`,
  };
}

function buildProjectCard(project: ProjectRollupRecord): ProjectCard {
  const budgetLabel = primaryAssetLabel(projectBudgetAssets(project));
  const proposal = project.proposal_summaries[0];
  const categoryLabel = project.scope_labels?.[0] || titleCase(project.category);
  return {
    id: project.project_id,
    href: projectHref(project.project_id),
    title: project.name,
    status: titleCase(project.status),
    category: categoryLabel,
    summary: truncate(project.objective, 180),
    proposalTag: proposal?.proposal_number !== null && proposal?.proposal_number !== undefined ? `Prop #${proposal.proposal_number}` : project.origin_proposals[0] ?? "No prop",
    budgetLabel,
    updatedAt: project.last_update_date ? formatDate(project.last_update_date) : "No updates yet",
    spentLabel: primaryAssetLabel(projectSpentAssets(project)),
    statusKey: project.status,
    categoryKey: categoryLabel,
    proofCount: project.proof_count ?? 0,
    deliveryCount: project.delivery_count ?? 0,
    searchText: `${project.name} ${project.objective} ${project.category} ${project.status} ${(project.branding_tags ?? []).join(" ")}`,
  };
}

function buildProposalCard(
  proposal: ProposalEnrichedRecord,
  projectsByArchiveId: Map<string, ProjectRollupRecord>,
): ProposalCard {
  const budgetLabel = proposal.routed_total_display !== "No direct spend"
    ? proposal.routed_total_display
    : proposal.requested_total_display;
  const project = projectsByArchiveId.get(proposal.archive_id);
  const labels = Array.from(
    new Set([
      ...proposal.editorial_labels,
      ...proposal.status_labels,
      ...proposal.funding_labels,
      ...proposal.relationship_labels,
      ...proposal.platform_labels,
      ...proposal.lifecycle_labels,
      ...proposal.proof_labels,
    ]),
  );
  return {
    archiveId: proposal.archive_id,
    href: proposalHref(proposal.archive_id),
    numberLabel: proposal.proposal_number !== null ? `Prop #${proposal.proposal_number}` : proposal.archive_id,
    title: proposal.title,
    status: titleCase(proposal.status),
    proposerLabel: proposal.proposer_label || proposal.proposer || "Unknown proposer",
    budgetLabel,
    summary: truncate(proposal.summary_short || proposal.summary, 180),
    projectLabel: project?.name ?? null,
    date: proposal.date,
    category: proposal.category,
    statusKey: proposal.status,
    routedValue: proposal.routed_by_asset.reduce((total, item) => total + item.amount, 0),
    voteCount: proposal.vote_count,
    hot: proposal.hot,
    labels,
    searchText: `${proposal.title} ${proposal.category} ${proposal.proposer_label ?? proposal.proposer} ${proposal.summary} ${proposal.summary_short} ${proposal.primary_recipients.join(" ")} ${labels.join(" ")}`,
  };
}

function buildTimelineCard(
  event: TimelineEventRecord,
  peopleByAddress: Map<string, PersonRecord>,
): TimelineCard {
  const people = uniqueBy(
    event.people_addresses
      .map((address) => peopleByAddress.get(address.toLowerCase()))
      .filter((person): person is PersonRecord => Boolean(person))
      .map((person) => ({
        label: person.display_name,
        href: communityHref(person.slug),
      })),
    (item) => item.href,
  );
  return {
    eventId: event.event_id,
    date: event.date,
    kind: titleCase(event.kind),
    status: titleCase(event.status),
    dateLabel: formatDate(event.date),
    title: event.title,
    summary: truncate(event.summary, 220),
    href: timelineHref(event),
    people,
    project: event.project_id && event.project_name ? { label: event.project_name, href: projectHref(event.project_id) } : null,
  };
}

function ensureDirForRoute(routePath: string) {
  if (routePath === "/") {
    return path.join(distDir, "index.html");
  }
  const cleaned = routePath.replace(/^\/+|\/+$/g, "");
  return path.join(distDir, cleaned, "index.html");
}

function assetLinksFromManifest(manifest: Record<string, { file: string; css?: string[] }>) {
  const entry = manifest["index.html"];
  if (!entry) {
    throw new Error("Unable to find index.html entry in Vite manifest");
  }
  return {
    scriptHref: `/${entry.file}`,
    styleHrefs: (entry.css ?? []).map((css) => `/${css}`),
  };
}

function requireItem<T>(value: T | undefined, message: string): T {
  if (value === undefined) {
    throw new Error(message);
  }
  return value;
}

function assertUniquePathnames(payloads: PagePayload[]) {
  const seen = new Set<string>();
  for (const payload of payloads) {
    if (seen.has(payload.meta.pathname)) {
      throw new Error(`Duplicate prerender pathname detected: ${payload.meta.pathname}`);
    }
    seen.add(payload.meta.pathname);
  }
}

function assertNetworkViewIntegrity(view: NetworkViewData) {
  const nodeIds = new Set(view.nodes.map((node) => node.node_id));
  for (const edge of view.edges) {
    if (!nodeIds.has(edge.source) || !nodeIds.has(edge.target)) {
      throw new Error(`Network edge ${edge.edge_id} references a missing node`);
    }
    if (edge.sourceNode.node_id !== edge.source || edge.targetNode.node_id !== edge.target) {
      throw new Error(`Network edge ${edge.edge_id} has mismatched embedded node references`);
    }
  }
}

function documentHtml(payload: PagePayload, appHtml: string, assets: { scriptHref: string; styleHrefs: string[] }) {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="${payload.meta.description.replace(/"/g, "&quot;")}" />
    <title>${payload.meta.title}</title>
    ${assets.styleHrefs.map((href) => `<link rel="stylesheet" href="${href}" />`).join("\n    ")}
  </head>
  <body>
    <div id="root">${appHtml}</div>
    <script>window.__GNARS_PAGE_PAYLOAD__=${htmlEscapeJson(payload)};</script>
    <script type="module" crossorigin src="${assets.scriptHref}"></script>
  </body>
</html>`;
}

function buildSceneFromPoints(
  windowId: string,
  label: string,
  points: { index: number; date: string; governance: number; treasury: number; deliveries: number }[],
): ActivityViewScene {
  const width = 1080;
  const height = 240;
  const left = 14;
  const top = 16;
  const bottom = 20;
  const right = 14;
  const safePoints = points.length
    ? points
    : [{ index: 0, date: "", governance: 0, treasury: 0, deliveries: 0 }];
  const maxValue = Math.max(1, ...safePoints.flatMap((point) => [point.governance, point.treasury, point.deliveries]));
  const x = scaleLinear().domain([0, Math.max(1, safePoints.length - 1)]).range([left, width - right]);
  const y = scaleLinear().domain([0, maxValue]).range([height - bottom, top]);
  const buildPath = (key: "governance" | "treasury" | "deliveries") =>
    line<{ index: number; governance: number; treasury: number; deliveries: number }>()
      .x((point) => x(point.index))
      .y((point) => y(point[key]))
      .curve(curveMonotoneX)(safePoints);

  return {
    window_id: windowId,
    label,
    width,
    height,
    max_value: maxValue,
    points: safePoints,
    paths: {
      governance: buildPath("governance"),
      treasury: buildPath("treasury"),
      deliveries: buildPath("deliveries"),
    },
  };
}

function buildPersonActivityScene(
  person: PersonRecord,
  authored: ProposalArchiveRecord[],
  participation: ProposalArchiveRecord[],
  proofOfWork: TimelineCard[],
  spendLedger: SpendLedgerRecord[],
): ActivityViewScene {
  const buckets = new Map<string, { governance: number; treasury: number; deliveries: number }>();
  const touch = (date: string, key: "governance" | "treasury" | "deliveries", value: number) => {
    const row = buckets.get(date) ?? { governance: 0, treasury: 0, deliveries: 0 };
    row[key] += value;
    buckets.set(date, row);
  };

  for (const proposal of authored) {
    touch(proposal.end_at.slice(0, 10), "governance", 1);
  }
  for (const proposal of participation) {
    touch(proposal.end_at.slice(0, 10), "governance", 0.5);
  }
  for (const record of spendLedger.filter((item) => item.recipient_address.toLowerCase() === person.address.toLowerCase())) {
    const day = (record.proposal_end_at || record.proposal_created_at || "").slice(0, 10);
    if (day) {
      touch(day, "treasury", 1);
    }
  }
  for (const event of proofOfWork) {
    if (event.date) {
      touch(event.date.slice(0, 10), "deliveries", 1);
    }
  }

  const orderedDates = [...buckets.keys()].sort();
  const points = orderedDates.slice(-90).map((date, index) => ({
    index,
    date,
    governance: buckets.get(date)?.governance ?? 0,
    treasury: buckets.get(date)?.treasury ?? 0,
    deliveries: buckets.get(date)?.deliveries ?? 0,
  }));
  return buildSceneFromPoints("profile-90d", "Profile Activity", points);
}

function neighborhoodForPerson(
  person: PersonRecord,
  networkView: NetworkViewData,
): CommunityProfilePageProps["networkNeighbors"] {
  const nodeId = `person:${person.address.toLowerCase()}`;
  const nodeById = new Map(networkView.nodes.map((node) => [node.node_id, node]));
  return networkView.edges
    .filter((edge) => edge.source === nodeId || edge.target === nodeId)
    .map((edge) => {
      const otherId = edge.source === nodeId ? edge.target : edge.source;
      const node = nodeById.get(otherId);
      return {
        label: node?.label ?? otherId,
        href: node?.href ?? "#",
        kind: titleCase(node?.kind ?? "unknown"),
        relationship: titleCase(edge.kind),
        valueLabel: edge.asset_symbol ? formatAmount(edge.asset_symbol, edge.weight) : `${edge.count}`,
        numericValue: edge.asset_symbol ? Number(edge.weight) : Number(edge.count),
      };
    })
    .sort((left, right) => right.numericValue - left.numericValue || left.label.localeCompare(right.label))
    .slice(0, 12);
}

async function main() {
  const peopleData = await loadJson<{ records: PersonRecord[] }>("people.json");
  const spendLedgerData = await loadJson<{ records: SpendLedgerRecord[] }>("spend_ledger.json");
  const projectsData = await loadJson<{ records: ProjectRollupRecord[] }>("project_rollups.json");
  const proposalsData = await loadJson<{ records: ProposalArchiveRecord[] }>("proposals_archive.json");
  const proposalsEnrichedData = await loadJson<ProposalEnrichedData>("proposals_enriched.json");
  const timelineData = await loadJson<{ records: TimelineEventRecord[] }>("timeline_events.json");
  const metricsData = await loadJson<DaoMetrics>("dao_metrics.json");
  const notesData = await loadJson<{ records: NotesIndexRecord[] }>("notes_index.json");
  const communitySignalsData = await loadJson<CommunitySignalsData>("community_signals.json");
  const feedStreamData = await loadJson<FeedStreamData>("feed_stream.json");
  const insightsData = await loadJson<InsightsData>("insights.json");
  const filterFacetsData = await loadJson<FilterFacetsData>("filter_facets.json");
  const activityTimeseriesData = await loadJson<ActivityTimeseriesData>("activity_timeseries.json");
  const activityViewData = await loadJson<ActivityViewData>("activity_view.json");
  const treasuryFlowsData = await loadJson<TreasuryFlowsData>("treasury_flows.json");
  const treasuryViewData = await loadJson<TreasuryViewData>("treasury_view.json");
  const networkViewData = await loadJson<NetworkViewData>("network_view.json");

  const people = peopleData.records;
  const spendLedger = spendLedgerData.records;
  const projects = projectsData.records;
  const proposals = proposalsData.records;
  const proposalsEnriched = proposalsEnrichedData.records;
  const timeline = timelineData.records;
  const notes = notesData.records;

  const peopleByAddress = new Map(people.map((person) => [person.address.toLowerCase(), person]));
  const projectsById = new Map(projects.map((project) => [project.project_id, project]));
  const proposalsEnrichedById = new Map(proposalsEnriched.map((proposal) => [proposal.archive_id, proposal]));
  const proposalsByAlias = new Map<string, ProposalArchiveRecord>();
  for (const proposal of proposals) {
    for (const alias of proposalAliases(proposal)) {
      proposalsByAlias.set(alias, proposal);
    }
  }
  const projectsByArchiveId = new Map<string, ProjectRollupRecord>();
  for (const project of projects) {
    for (const summary of project.proposal_summaries) {
      projectsByArchiveId.set(summary.archive_id, project);
    }
  }
  const budgetMap = buildProposalBudgetMap(spendLedger);
  const communityCards = people.map((person) => buildCommunityCard(person, spendLedger, proposals));
  const filters = ["All", ...uniqueBy(communityCards.flatMap((card) => card.tribes.map((tribe) => ({ tribe }))), (item) => item.tribe).map((item) => item.tribe)];
  const projectCards = projects.map(buildProjectCard);
  const projectFilters = ["All", ...uniqueBy(projectCards.map((project) => ({ category: project.category })), (item) => item.category).map((item) => item.category)];
  const proposalCards = proposalsEnriched
    .slice()
    .sort((left, right) => `${right.date}${right.archive_id}`.localeCompare(`${left.date}${left.archive_id}`))
    .map((proposal) => buildProposalCard(proposal, projectsByArchiveId));
  const timelineCards = timeline.map((event) => buildTimelineCard(event, peopleByAddress));
  assertNetworkViewIntegrity(networkViewData);

  const signalWindow = requireItem(
    communitySignalsData.windows.find((window) => window.window_id === "30d") ?? communitySignalsData.windows[0],
    "Missing community signal window for prerender",
  );
  const treasuryScene = requireItem(
    treasuryViewData.scenes.find((scene) => scene.window_id === "30d") ?? treasuryViewData.scenes[0],
    "Missing treasury scene for prerender",
  );
  const activityScene = requireItem(
    activityViewData.scenes.find((scene) => scene.window_id === "30d") ?? activityViewData.scenes[0],
    "Missing activity scene for prerender",
  );

  const payloads: PagePayload[] = [];

  payloads.push({
    pageType: "home",
    meta: {
      title: "Gnars Camp",
      description: "Research-grade community atlas of Gnars: treasury, governance, people, and delivery.",
      pathname: "/",
      activeNav: "home",
    },
    props: {
      analyticsAsOf: feedStreamData.analytics_as_of,
      asOf: communitySignalsData.as_of,
      hero: {
        title: "A live operating surface for how Gnars routes capital, builds culture, and ships work.",
        description:
          "Read Gnars as one mixed feed: proposals, payouts, workstreams, people, and proof. The point is multiplicity without losing legibility.",
      },
      metrics: [
        { label: "People", value: String(metricsData.overview.people_count), detail: "merged identities and participants" },
        { label: "Proposals", value: String(metricsData.overview.proposal_count), detail: "archived across gnars and snapshot" },
        { label: "Treasury", value: `$${Math.round(metricsData.overview.treasury_total_value_usd).toLocaleString("en-US")}`, detail: "current holdings view" },
        {
          label: "Concentration",
          value: `${Math.round(insightsData.recipient_concentration[0]?.top10_share_pct ?? 0)}%`,
          detail: "top-10 USDC recipient share",
        },
      ],
      economicMap: networkViewData,
      activity: activityScene,
      treasuryScene,
      signalWindow,
      fieldNotes: communitySignalsData.field_notes,
      feed: feedStreamData.records.slice(0, 80),
      facets: filterFacetsData.surfaces.home,
      insights: insightsData,
      featuredCommunity: communityCards
        .slice()
        .sort((left, right) => Number(right.featured) - Number(left.featured) || right.proofCount - left.proofCount || right.approvedProposals - left.approvedProposals)
        .slice(0, 8),
      featuredProjects: projectCards.slice().sort((left, right) => right.proofCount - left.proofCount || right.deliveryCount - left.deliveryCount).slice(0, 6),
      governance: proposalCards.slice(0, 8),
      timeline: timelineCards.slice(0, 8),
      leaderboards: [
        {
          title: "ETH Received",
          items: metricsData.leaderboards.eth_received.slice(0, 5).map((item) => ({
            label: item.display_name,
            value: formatAmount("ETH", item.value),
            href: communityHref(item.slug),
          })),
        },
        {
          title: "USDC Received",
          items: metricsData.leaderboards.usdc_received.slice(0, 5).map((item) => ({
            label: item.display_name,
            value: formatAmount("USDC", item.value),
            href: communityHref(item.slug),
          })),
        },
        {
          title: "Proposals Authored",
          items: metricsData.leaderboards.proposal_count.slice(0, 5).map((item) => ({
            label: item.display_name,
            value: `${item.value}`,
            href: communityHref(item.slug),
          })),
        },
      ],
    },
  });

  payloads.push({
    pageType: "community-index",
    meta: {
      title: "Community - Gnars Camp",
      description: "Unified community directory for athletes, builders, organizers, and governance participants.",
      pathname: "/community/",
      activeNav: "community",
    },
    props: {
      filters,
      facets: filterFacetsData.surfaces.community,
      people: communityCards,
      economicMap: networkViewData,
    } satisfies CommunityIndexPageProps,
  });

  for (const person of people) {
    const authored = person.relationships.authored_proposals
      .map((reference) => proposalsByAlias.get(reference.toLowerCase()))
      .filter((proposal): proposal is ProposalArchiveRecord => Boolean(proposal))
      .sort((left, right) => right.end_at.localeCompare(left.end_at));
    const participation = uniqueBy(
      [...person.relationships.voted_proposals, ...person.relationships.payout_proposals]
        .map((reference) => proposalsByAlias.get(reference.toLowerCase()))
        .filter((proposal): proposal is ProposalArchiveRecord => Boolean(proposal))
        .sort((left, right) => right.end_at.localeCompare(left.end_at)),
      (proposal) => proposal.archive_id,
    );
    const economics = getAthleteEconomics(person.address, spendLedger, proposals, person.relationships.owned_projects);
    const relatedProjects = uniqueBy(
      [...person.relationships.owned_projects, ...person.relationships.related_projects]
        .map((projectId) => projectsById.get(projectId))
        .filter((project): project is ProjectRollupRecord => Boolean(project))
        .map((project) => ({
          label: project.name,
          href: projectHref(project.project_id),
        })),
      (item) => item.href,
    );
    const proofOfWork = timelineCards
      .filter((event) => {
        if (event.people.some((item) => item.href === communityHref(person.slug))) {
          return true;
        }
        if (relatedProjects.some((project) => project.href === event.project?.href)) {
          return true;
        }
        return authored.some((proposal) => proposalHref(proposal.archive_id) === event.href);
      })
      .slice(0, 12);
    const identityLinks = [
      person.identity.member_url ? { label: "Gnars member page", url: person.identity.member_url, kind: "Member" } : null,
      person.identity.farcaster ? { label: "Farcaster", url: person.identity.farcaster, kind: "Social" } : null,
      person.identity.github ? { label: "GitHub", url: person.identity.github, kind: "Code" } : null,
      person.identity.website ? { label: "Website", url: person.identity.website, kind: "Web" } : null,
      person.identity.x ? { label: "X", url: person.identity.x, kind: "Social" } : null,
      person.identity.instagram ? { label: "Instagram", url: person.identity.instagram, kind: "Social" } : null,
    ].filter((item): item is NonNullable<typeof item> => Boolean(item));

    const profilePayload: PagePayload = {
      pageType: "community-profile",
      meta: {
        title: `${person.display_name} - Gnars Camp`,
        description: `Treasury, governance, and delivery dossier for ${person.display_name}.`,
        pathname: communityHref(person.slug),
        activeNav: "community",
      },
      props: {
        profile: {
          displayName: personLabel(person),
          address: person.address,
          addressShort: person.address_short,
          tribes: tribeLabels(person.tribes?.length ? person.tribes : person.tags),
          role: person.role,
          bio: person.history_short || person.bio,
          links: [
            ...identityLinks,
            ...person.media_references.slice(0, 4).map((reference) => ({
              label: reference.title,
              url: reference.url,
              kind: titleCase(reference.kind),
            })),
          ],
          avatarUrl: person.identity.avatar_url ?? null,
        },
        economics,
        governanceMetrics: {
          activeVotes: person.governance.active_votes,
          votesCast: person.governance.votes_cast_count,
          attendancePct: person.governance.attendance_pct,
          likePct: person.governance.like_pct,
          proposalSuccessRate: authored.length
            ? Math.round((authored.filter((proposal) => isSuccessfulProposal(proposal)).length / authored.length) * 100)
            : 0,
          deliveryCount: proofOfWork.length,
        },
        governanceLog: authored.map((proposal) => ({
          href: proposalHref(proposal.archive_id),
          numberLabel: proposal.proposal_number !== null ? `Prop #${proposal.proposal_number}` : proposal.archive_id,
          title: proposal.title,
          status: titleCase(proposal.status),
          budgetLabel: proposalBudgetLabel(budgetMap.get(proposal.archive_id) ?? []),
          endedAt: formatDate(proposal.end_at),
        })),
        participation: participation.slice(0, 16).map((proposal) => ({
          href: proposalHref(proposal.archive_id),
          numberLabel: proposal.proposal_number !== null ? `Prop #${proposal.proposal_number}` : proposal.archive_id,
          title: proposal.title,
          status: titleCase(proposal.status),
        })),
        projects: relatedProjects,
        proofOfWork,
        activity: buildPersonActivityScene(person, authored, participation, proofOfWork, spendLedger),
        networkNeighbors: neighborhoodForPerson(person, networkViewData),
      } satisfies CommunityProfilePageProps,
    };
    payloads.push(profilePayload);
  }

  payloads.push({
    pageType: "projects-index",
    meta: {
      title: "Projects - Gnars Camp",
      description: "Treasury-linked workstreams and projects across Gnars.",
      pathname: "/projects/",
      activeNav: "projects",
    },
    props: {
      filters: projectFilters,
      facets: filterFacetsData.surfaces.projects,
      projects: projectCards,
      featuredLineage: treasuryScene,
    },
  });

  for (const project of projects) {
    const card = buildProjectCard(project);
    const timelineForProject = timelineCards.filter((event) => event.project?.href === projectHref(project.project_id)).slice(0, 12);
    const projectPayload: PagePayload = {
      pageType: "project-detail",
      meta: {
        title: `${project.name} - Gnars Camp`,
        description: truncate(project.objective, 150),
        pathname: projectHref(project.project_id),
        activeNav: "projects",
      },
      props: {
        project: {
          ...card,
          objective: project.objective,
          outputs: project.outputs,
          kpis: project.kpis,
          budgetByAsset: projectBudgetAssets(project),
          spentByAsset: projectSpentAssets(project),
          utilization: [
            project.utilization_pct.eth !== null ? { label: "ETH", value: `${project.utilization_pct.eth}% ETH` } : null,
            project.utilization_pct.usdc !== null ? { label: "USDC", value: `${project.utilization_pct.usdc}% USDC` } : null,
            project.utilization_pct.gnars !== null ? { label: "GNARS", value: `${project.utilization_pct.gnars}% GNARS` } : null,
          ].filter((item): item is { label: string; value: string } => Boolean(item)),
          recipients: project.recipients.map((recipient) => {
            const linked = peopleByAddress.get(recipient.address.toLowerCase());
            return {
              label: recipient.display_name,
              href: linked ? communityHref(linked.slug) : "#",
              amounts: [
                { symbol: "ETH", amount: recipient.eth_received },
                { symbol: "USDC", amount: recipient.usdc_received },
                { symbol: "GNARS", amount: recipient.gnars_received },
              ].filter((item) => item.amount > 0),
            };
          }),
          proposalLinks: project.proposal_summaries.map((summary) => ({
            label: summary.proposal_number !== null ? `Prop #${summary.proposal_number} - ${summary.title}` : summary.title,
            href: proposalHref(summary.archive_id),
          })),
          timeline: timelineForProject,
          recipientDistribution: projectSpentAssets(project),
          treasuryScene: null,
        },
      } satisfies ProjectDetailPageProps,
    };
    payloads.push(projectPayload);
  }

  payloads.push({
    pageType: "proposals-index",
    meta: {
      title: "Governance - Gnars Camp",
      description: "Readable history of Gnars governance across proposals and treasury routing.",
      pathname: "/proposals/",
      activeNav: "governance",
    },
    props: {
      proposals: proposalCards,
      signals: signalWindow,
      facets: filterFacetsData.surfaces.proposals,
    },
  });

  for (const proposal of proposals) {
    const enriched = proposalsEnrichedById.get(proposal.archive_id);
    if (!enriched) {
      continue;
    }
    const card = buildProposalCard(enriched, projectsByArchiveId);
    const groupedRecipients = new Map<string, SpendLedgerRecord[]>();
    for (const record of budgetMap.get(proposal.archive_id) ?? []) {
      const records = groupedRecipients.get(record.recipient_address) ?? [];
      records.push(record);
      groupedRecipients.set(record.recipient_address, records);
    }
    const relatedPeople = uniqueBy(
      [
        peopleByAddress.get(proposal.proposer.toLowerCase()),
        ...[...groupedRecipients.keys()].map((address) => peopleByAddress.get(address.toLowerCase())),
      ]
        .filter((person): person is PersonRecord => Boolean(person))
        .map((person) => ({
          label: person.display_name,
          href: communityHref(person.slug),
        })),
      (item) => item.href,
    );
    const linkedProject = projectsByArchiveId.get(proposal.archive_id);
    const proposalPayload: PagePayload = {
      pageType: "proposal-detail",
      meta: {
        title: `${card.numberLabel} - ${proposal.title}`,
        description: truncate(proposal.content_summary, 150),
        pathname: proposalHref(proposal.archive_id),
        activeNav: "governance",
      },
      props: {
        proposal: {
          ...card,
          createdAt: formatDate(proposal.created_at),
          endAt: formatDate(proposal.end_at),
          choices: proposal.choices,
          scoresByChoice: proposal.scores_by_choice,
          contentSummary: proposal.content_summary,
          proposalLinks: [
            { label: "Canonical", url: proposal.links.canonical_url, kind: "Web" },
            { label: "Source", url: proposal.links.source_url, kind: "Source" },
            ...(proposal.links.discussion_url ? [{ label: "Discussion", url: proposal.links.discussion_url, kind: "Discussion" }] : []),
            ...(proposal.links.explorer_url ? [{ label: "Explorer", url: proposal.links.explorer_url, kind: "Explorer" }] : []),
            ...enriched.reference_urls
              .filter((url) => ![proposal.links.canonical_url, proposal.links.source_url, proposal.links.discussion_url, proposal.links.explorer_url].includes(url))
              .slice(0, 4)
              .map((url) => ({ label: url.replace(/^https?:\/\//, "").slice(0, 42), url, kind: "Reference" })),
          ],
          recipients: [...groupedRecipients.entries()].map(([address, records]) => {
            const linked = peopleByAddress.get(address.toLowerCase());
            return {
              label: linked?.display_name ?? records[0].recipient_display_name,
              href: linked ? communityHref(linked.slug) : null,
              amounts: groupAssetTotals(records),
            };
          }),
          relatedPeople,
          relatedProject: linkedProject ? { label: linkedProject.name, href: projectHref(linkedProject.project_id) } : null,
          flowLineage: groupAssetTotals(budgetMap.get(proposal.archive_id) ?? []),
          treasuryScene: null,
        },
      } satisfies ProposalDetailPageProps,
    };
    payloads.push(proposalPayload);
  }

  payloads.push({
    pageType: "timeline-index",
    meta: {
      title: "Timeline - Gnars Camp",
      description: "Chronology of governance, workstreams, and public proof across Gnars.",
      pathname: "/timeline/",
      activeNav: "timeline",
    },
    props: {
      timeline: timelineCards,
      activity: requireItem(
        activityViewData.scenes.find((scene) => scene.window_id === "90d") ?? activityScene,
        "Missing timeline activity scene for prerender",
      ),
    },
  });

  payloads.push({
    pageType: "network-index",
    meta: {
      title: "Network - Gnars Camp",
      description: "Economic map of people, proposals, projects, and treasury routes across Gnars.",
      pathname: "/network/",
      activeNav: "network",
    },
    props: {
      scene: networkViewData,
      highlights: [
        {
          title: "Top Recipients",
          items: signalWindow.top_recipients.slice(0, 6).map((item) => {
            const linked = peopleByAddress.get(item.address.toLowerCase());
            return {
              label: item.display_name,
              detail: item.totals_by_asset.map((asset) => formatAmount(asset.symbol, asset.amount)).join(" + "),
              href: linked ? communityHref(linked.slug) : "#",
            };
          }),
        },
        {
          title: "Top Projects",
          items: signalWindow.top_projects.slice(0, 6).map((item) => ({
            label: item.project_name,
            detail: item.totals_by_asset.map((asset) => formatAmount(asset.symbol, asset.amount)).join(" + "),
            href: projectHref(item.project_id),
          })),
        },
        {
          title: "Top Proposals",
          items: signalWindow.top_proposals.slice(0, 6).map((item) => ({
            label: item.proposal_number !== null ? `Prop #${item.proposal_number}` : item.title,
            detail: item.totals_by_asset.map((asset) => formatAmount(asset.symbol, asset.amount)).join(" + "),
            href: proposalHref(item.archive_id),
          })),
        },
      ],
    } satisfies NetworkPageProps,
  });

  payloads.push({
    pageType: "treasury-index",
    meta: {
      title: "Treasury - Gnars Camp",
      description: "Treasury routing and proposal-to-recipient flow across Gnars.",
      pathname: "/treasury/",
      activeNav: "treasury",
    },
    props: {
      treasuryScene: treasuryViewData,
      windows: treasuryFlowsData.windows,
      proposalRoutes: treasuryFlowsData.proposal_routes,
      insights: insightsData,
      facets: filterFacetsData.surfaces.treasury,
    } satisfies TreasuryPageProps,
  });

  payloads.push({
    pageType: "notes-index",
    meta: {
      title: "Archive - Gnars Camp",
      description: "Markdown archive and operational notes for Gnars DAO.",
      pathname: "/notes/",
      activeNav: "archive",
    },
    props: {
      notes,
    },
  });

  assertUniquePathnames(payloads);

  const manifest = JSON.parse(await fs.readFile(path.join(distDir, ".vite", "manifest.json"), "utf8")) as Record<string, { file: string; css?: string[] }>;
  const assets = assetLinksFromManifest(manifest);

  for (const payload of payloads) {
    const html = documentHtml(payload, renderPageMarkup(payload), assets);
    const outputPath = ensureDirForRoute(payload.meta.pathname);
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, html);
  }

  console.log(`[ok] prerendered ${payloads.length} static routes`);
}

await main();
