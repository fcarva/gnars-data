import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { renderPageMarkup } from "../src/entry-server";
import type {
  CommunityCard,
  CommunityProfilePageProps,
  DaoMetrics,
  NotesIndexRecord,
  PagePayload,
  PersonRecord,
  ProjectCard,
  ProjectDetailPageProps,
  ProjectRollupRecord,
  ProposalArchiveRecord,
  ProposalCard,
  ProposalDetailPageProps,
  SpendLedgerRecord,
  TimelineCard,
  TimelineEventRecord,
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
  return {
    slug: person.slug,
    href: communityHref(person.slug),
    displayName: person.display_name,
    subtitle: personSubtitle(person),
    tribes: tribeLabels(person.tags),
    totalReceivedLabel: economics.totalReceivedPrimary
      ? `Received ${formatAmount(economics.totalReceivedPrimary.symbol, economics.totalReceivedPrimary.amount)}`
      : "No successful treasury flows",
    approvedProposals: economics.approvedProposals,
    budgetManagedLabel: economics.budgetManagedByAsset.length
      ? `Managed ${economics.budgetManagedByAsset.map((item) => formatAmount(item.symbol, item.amount)).join(" + ")}`
      : "No approved managed budget",
    featured: person.tags.includes("athlete") || person.tags.includes("proposer") || person.tags.includes("recipient"),
  };
}

function buildProjectCard(project: ProjectRollupRecord): ProjectCard {
  const budgetLabel = primaryAssetLabel(projectBudgetAssets(project));
  const proposal = project.proposal_summaries[0];
  return {
    id: project.project_id,
    href: projectHref(project.project_id),
    title: project.name,
    status: titleCase(project.status),
    category: titleCase(project.category),
    summary: truncate(project.objective, 180),
    proposalTag: proposal?.proposal_number !== null && proposal?.proposal_number !== undefined ? `Prop #${proposal.proposal_number}` : project.origin_proposals[0] ?? "No prop",
    budgetLabel,
    updatedAt: project.last_update_date ? formatDate(project.last_update_date) : "No updates yet",
  };
}

function buildProposalCard(
  proposal: ProposalArchiveRecord,
  budgetMap: Map<string, SpendLedgerRecord[]>,
  projectsByArchiveId: Map<string, ProjectRollupRecord>,
): ProposalCard {
  const budgetLabel = proposalBudgetLabel(budgetMap.get(proposal.archive_id) ?? []);
  const project = projectsByArchiveId.get(proposal.archive_id);
  return {
    archiveId: proposal.archive_id,
    href: proposalHref(proposal.archive_id),
    numberLabel: proposal.proposal_number !== null ? `Prop #${proposal.proposal_number}` : proposal.archive_id,
    title: proposal.title,
    status: titleCase(proposal.status),
    proposerLabel: proposal.proposer_label || proposal.proposer,
    budgetLabel,
    summary: truncate(proposal.content_summary, 180),
    projectLabel: project?.name ?? null,
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

async function main() {
  const peopleData = await loadJson<{ records: PersonRecord[] }>("people.json");
  const spendLedgerData = await loadJson<{ records: SpendLedgerRecord[] }>("spend_ledger.json");
  const projectsData = await loadJson<{ records: ProjectRollupRecord[] }>("project_rollups.json");
  const proposalsData = await loadJson<{ records: ProposalArchiveRecord[] }>("proposals_archive.json");
  const timelineData = await loadJson<{ records: TimelineEventRecord[] }>("timeline_events.json");
  const metricsData = await loadJson<DaoMetrics>("dao_metrics.json");
  const notesData = await loadJson<{ records: NotesIndexRecord[] }>("notes_index.json");

  const people = peopleData.records;
  const spendLedger = spendLedgerData.records;
  const projects = projectsData.records;
  const proposals = proposalsData.records;
  const timeline = timelineData.records;
  const notes = notesData.records;

  const peopleByAddress = new Map(people.map((person) => [person.address.toLowerCase(), person]));
  const peopleBySlug = new Map(people.map((person) => [person.slug, person]));
  const projectsById = new Map(projects.map((project) => [project.project_id, project]));
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
  const proposalCards = proposals
    .slice()
    .sort((left, right) => `${right.end_at}${right.created_at}`.localeCompare(`${left.end_at}${left.created_at}`))
    .map((proposal) => buildProposalCard(proposal, budgetMap, projectsByArchiveId));
  const timelineCards = timeline.map((event) => buildTimelineCard(event, peopleByAddress));

  const payloads: PagePayload[] = [];

  payloads.push({
    pageType: "home",
    meta: {
      title: "Gnars Camp",
      description: "Community, governance, treasury, and delivery mapped into one static Gnars atlas.",
      pathname: "/",
      activeNav: "home",
    },
    props: {
      hero: {
        title: "A static atlas of how Gnars allocates capital, builds culture, and ships work.",
        description:
          "Gnars Camp fuses editorial storytelling with linked governance data, so every athlete, builder, filmmaker, proposal, and workstream becomes part of one public economic graph.",
      },
      metrics: [
        { label: "People", value: String(metricsData.overview.people_count), detail: "merged identities and DAO participants" },
        { label: "Proposals", value: String(metricsData.overview.proposal_count), detail: "archived across gnars and snapshot" },
        { label: "Treasury", value: `$${Math.round(metricsData.overview.treasury_total_value_usd).toLocaleString("en-US")}`, detail: "current holdings view" },
        { label: "Outflows", value: `${metricsData.overview.outflows_eth.toFixed(2)} ETH`, detail: "successful routed treasury flows" },
      ],
      featuredCommunity: communityCards
        .slice()
        .sort((left, right) => Number(right.featured) - Number(left.featured) || right.approvedProposals - left.approvedProposals)
        .slice(0, 8),
      featuredProjects: projectCards.slice(0, 6),
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
      people: communityCards,
    },
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
          tribes: tribeLabels(person.tags),
          role: person.role,
          bio: person.bio,
          links: identityLinks,
          avatarUrl: person.identity.avatar_url ?? null,
        },
        economics,
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
      projects: projectCards,
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
    },
  });

  for (const proposal of proposals) {
    const card = buildProposalCard(proposal, budgetMap, projectsByArchiveId);
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
    },
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
