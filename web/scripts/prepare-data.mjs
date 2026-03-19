import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
} from "d3-force";
import { sankey, sankeyLinkHorizontal } from "d3-sankey";
import { scaleLinear } from "d3-scale";
import { curveMonotoneX, line } from "d3-shape";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(webRoot, "..");
const dataDir = path.join(repoRoot, "data");
const docsDir = path.join(repoRoot, "docs");
const publicDataDir = path.join(webRoot, "public", "data");

function toPosix(value) {
  return value.split(path.sep).join("/");
}

function stripMarkdown(value) {
  return value
    .replace(/!\[[^\]]*]\([^)]*\)/g, "")
    .replace(/\[[^\]]*]\(([^)]*)\)/g, "$1")
    .replace(/[`*_>#-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

async function readJson(filename) {
  return JSON.parse(await fs.readFile(path.join(dataDir, filename), "utf8"));
}

async function walkMarkdown(directory) {
  const entries = await fs.readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await walkMarkdown(fullPath)));
    } else if (entry.isFile() && entry.name.endsWith(".md")) {
      files.push(fullPath);
    }
  }
  return files;
}

function headingFromContent(content, fallback) {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : fallback;
}

function excerptFromContent(content) {
  const cleaned = stripMarkdown(content).replace(
    /\b(?:csv|json|curl|download(?:able)?|exports?|datasets?)\b/gi,
    "",
  );
  return cleaned.length > 220 ? `${cleaned.slice(0, 217)}...` : cleaned;
}

function sumAmount(items, amountKey = "amount") {
  return Number(
    items.reduce((total, item) => total + Number(item?.[amountKey] ?? 0), 0).toFixed(8),
  );
}

function seedRandom(seed = 42) {
  let state = seed >>> 0;
  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function laneX(kind, width) {
  if (kind === "treasury") return width * 0.12;
  if (kind === "proposal") return width * 0.4;
  if (kind === "project") return width * 0.67;
  return width * 0.88;
}

function buildNetworkView(networkGraph) {
  const width = 1480;
  const height = 860;
  const voteEdges = networkGraph.edges.filter((edge) => edge.kind === "voted");
  const nonVoteEdges = networkGraph.edges.filter((edge) => edge.kind !== "voted");
  const reducedVoteEdges = voteEdges
    .slice()
    .sort((left, right) => Number(right.count ?? 0) - Number(left.count ?? 0) || right.edge_id.localeCompare(left.edge_id))
    .slice(0, 900);
  const edges = [...nonVoteEdges, ...reducedVoteEdges];
  const activeNodeIds = new Set(edges.flatMap((edge) => [edge.source, edge.target]));
  const nodes = networkGraph.nodes
    .filter((node) => activeNodeIds.has(node.node_id))
    .map((node, index) => ({
      ...node,
      x: laneX(node.kind, width),
      y: 80 + ((index * 37) % (height - 160)),
      fx: undefined,
      fy: undefined,
    }));

  const simulation = forceSimulation(nodes)
    .randomSource(seedRandom(42))
    .force(
      "link",
      forceLink(
        edges.map((edge) => ({ ...edge })),
      )
        .id((node) => node.node_id)
        .distance((edge) => {
          if (edge.kind === "funded") return 110;
          if (edge.kind === "authored" || edge.kind === "managed") return 85;
          return 65;
        })
        .strength((edge) => (edge.kind === "funded" ? 0.18 : 0.08)),
    )
    .force("charge", forceManyBody().strength((node) => (node.kind === "treasury" ? -900 : -180)))
    .force("x", forceX((node) => laneX(node.kind, width)).strength(0.28))
    .force("y", forceY(height / 2).strength(0.045))
    .force("collide", forceCollide((node) => Math.max(16, Number(node.size ?? 18) * 0.48)))
    .force("center", forceCenter(width / 2, height / 2));

  for (let index = 0; index < 220; index += 1) {
    simulation.tick();
  }
  simulation.stop();

  const nodeMap = new Map(
    nodes.map((node) => [
      node.node_id,
      {
        ...node,
        x: Math.max(44, Math.min(width - 44, Number(node.x ?? width / 2))),
        y: Math.max(44, Math.min(height - 44, Number(node.y ?? height / 2))),
        radius: Math.max(7, Math.min(28, Number(node.size ?? 18) * 0.32)),
      },
    ]),
  );

  const homepageNodeIds = new Set(networkGraph.views.homepage.node_ids);
  const homepageEdgeIds = new Set(networkGraph.views.homepage.edge_ids);
  const graphEdges = edges
    .filter((edge) => nodeMap.has(edge.source) && nodeMap.has(edge.target))
    .map((edge) => {
      const source = nodeMap.get(edge.source);
      const target = nodeMap.get(edge.target);
      return {
        ...edge,
        sourceNode: source,
        targetNode: target,
      };
    });

  return {
    dataset: "network_view",
    as_of: networkGraph.as_of,
    version: 1,
    width,
    height,
    nodes: [...nodeMap.values()],
    edges: graphEdges,
    homepage: {
      node_ids: [...homepageNodeIds],
      edge_ids: [...homepageEdgeIds],
    },
    filters: {
      tribes: [
        ...new Set(
          [...nodeMap.values()]
            .filter((node) => node.kind === "person")
            .flatMap((node) => node.tags ?? []),
        ),
      ].sort(),
      assets: [...new Set(graphEdges.map((edge) => edge.asset_symbol).filter(Boolean))].sort(),
      statuses: [...new Set([...nodeMap.values()].map((node) => node.status).filter(Boolean))].sort(),
    },
  };
}

function buildTreasuryScene(windowId, windowLabel, routes) {
  const width = 1380;
  const height = 840;
  const grouped = new Map();

  function pushLink(source, target, value, assetSymbol, href, sourceKind, targetKind) {
    const key = `${source}|${target}|${assetSymbol}`;
    if (!grouped.has(key)) {
      grouped.set(key, {
        source,
        target,
        value: 0,
        asset_symbol: assetSymbol,
        href,
        source_kind: sourceKind,
        target_kind: targetKind,
      });
    }
    grouped.get(key).value += Number(value ?? 0);
  }

  const treasuryId = "treasury:gnars";
  for (const route of routes) {
    const proposalId = `proposal:${route.archive_id}`;
    const recipientId = `recipient:${route.recipient_address}`;
    const asset = route.asset_symbol;
    pushLink(treasuryId, proposalId, route.amount, asset, `/proposals/${route.archive_id}/`, "treasury", "proposal");
    if (route.project_id) {
      const projectId = `project:${route.project_id}`;
      pushLink(proposalId, projectId, route.amount, asset, `/projects/${route.project_id}/`, "proposal", "project");
      pushLink(projectId, recipientId, route.amount, asset, `/community/${route.recipient_address}/`, "project", "recipient");
    } else {
      pushLink(proposalId, recipientId, route.amount, asset, route.proposal_href, "proposal", "recipient");
    }
  }

  const nodeMap = new Map();
  const links = [...grouped.values()].map((link) => {
    if (!nodeMap.has(link.source)) {
      const [kind, value] = link.source.split(":");
      nodeMap.set(link.source, {
        id: link.source,
        label: kind === "treasury" ? "Gnars Treasury" : value,
        kind,
      });
    }
    if (!nodeMap.has(link.target)) {
      const [kind, value] = link.target.split(":");
      nodeMap.set(link.target, {
        id: link.target,
        label: value,
        kind,
      });
    }
    return { ...link };
  });

  const proposalLabels = new Map(routes.map((route) => [`proposal:${route.archive_id}`, route.proposal_number ? `Prop #${route.proposal_number}` : route.proposal_title]));
  const projectLabels = new Map(routes.filter((route) => route.project_id).map((route) => [`project:${route.project_id}`, route.project_name]));
  const recipientLabels = new Map(routes.map((route) => [`recipient:${route.recipient_address}`, route.recipient_display_name]));

  for (const node of nodeMap.values()) {
    if (node.kind === "proposal") {
      node.label = proposalLabels.get(node.id) ?? node.label;
    } else if (node.kind === "project") {
      node.label = projectLabels.get(node.id) ?? node.label;
    } else if (node.kind === "recipient") {
      node.label = recipientLabels.get(node.id) ?? node.label;
    }
  }

  const sankeyGraph = sankey()
    .nodeId((node) => node.id)
    .nodeWidth(16)
    .nodePadding(18)
    .extent([
      [14, 14],
      [width - 14, height - 14],
    ])({
      nodes: [...nodeMap.values()].map((node) => ({ ...node })),
      links: links.map((link) => ({ ...link })),
    });

  const pathBuilder = sankeyLinkHorizontal();
  return {
    window_id: windowId,
    label: windowLabel,
    width,
    height,
    route_count: routes.length,
    total_value: sumAmount(routes),
    nodes: sankeyGraph.nodes.map((node) => ({
      id: node.id,
      label: node.label,
      kind: node.kind,
      x0: node.x0,
      x1: node.x1,
      y0: node.y0,
      y1: node.y1,
      value: Number(node.value ?? 0),
    })),
    links: sankeyGraph.links.map((link, index) => ({
      link_id: `${windowId}:${index}`,
      source: link.source.id,
      target: link.target.id,
      value: Number(link.value ?? 0),
      width: Number(link.width ?? 0),
      asset_symbol: link.asset_symbol,
      href: link.href,
      path: pathBuilder(link),
    })),
  };
}

function buildTreasuryView(treasuryFlows) {
  const scenes = [];
  for (const window of treasuryFlows.windows.filter((item) => ["7d", "30d", "90d", "all"].includes(item.window_id))) {
    const selected = treasuryFlows.routes.filter((route) =>
      window.since ? new Date(route.event_at) >= new Date(window.since) : true,
    );
    scenes.push(buildTreasuryScene(window.window_id, window.label, selected));
  }
  return {
    dataset: "treasury_view",
    as_of: treasuryFlows.as_of,
    version: 1,
    scenes,
  };
}

function buildActivityScene(windowId, label, records) {
  const width = 1080;
  const height = 240;
  const padding = { top: 16, right: 14, bottom: 20, left: 14 };
  const points = records.map((record, index) => ({
    index,
    date: record.date,
    governance:
      Number(record.proposals_created ?? 0) +
      Number(record.proposals_closed ?? 0) +
      Number(record.proposals_executed ?? 0),
    treasury: Number(record.payouts_count ?? 0),
    deliveries: Number(record.deliveries_count ?? 0) + Number(record.updates_count ?? 0),
  }));
  const maxValue = Math.max(
    1,
    ...points.flatMap((point) => [point.governance, point.treasury, point.deliveries]),
  );
  const x = scaleLinear().domain([0, Math.max(1, points.length - 1)]).range([padding.left, width - padding.right]);
  const y = scaleLinear().domain([0, maxValue]).range([height - padding.bottom, padding.top]);
  const buildPath = (key) =>
    line()
      .x((point) => x(point.index))
      .y((point) => y(point[key]))
      .curve(curveMonotoneX)(points);

  return {
    window_id: windowId,
    label,
    width,
    height,
    max_value: maxValue,
    points,
    paths: {
      governance: buildPath("governance"),
      treasury: buildPath("treasury"),
      deliveries: buildPath("deliveries"),
    },
  };
}

function buildActivityView(activityTimeseries) {
  const scenes = [
    buildActivityScene("30d", "Last 30 Days", activityTimeseries.records.slice(-30)),
    buildActivityScene("90d", "Last 90 Days", activityTimeseries.records.slice(-90)),
    buildActivityScene("all", "All Time", activityTimeseries.records),
  ];
  return {
    dataset: "activity_view",
    as_of: activityTimeseries.as_of,
    version: 1,
    scenes,
  };
}

async function buildNotesIndex() {
  const markdownFiles = await walkMarkdown(docsDir);
  markdownFiles.push(path.join(repoRoot, "README.md"));
  const records = [];
  for (const filePath of markdownFiles) {
    const relative = path.relative(repoRoot, filePath);
    const content = await fs.readFile(filePath, "utf8");
    const title = headingFromContent(content, path.basename(filePath, ".md"));
    const slug = toPosix(relative).replace(/[/.]+/g, "-").toLowerCase();
    const section = relative === "README.md" ? "root" : relative.split(path.sep)[0];
    records.push({
      slug,
      title,
      section,
      href: `/notes/#${slug}`,
      excerpt: excerptFromContent(content),
    });
  }
  records.sort((left, right) => left.title.localeCompare(right.title));
  return {
    dataset: "notes_index",
    as_of: new Date().toISOString(),
    version: 1,
    records,
  };
}

async function buildSearchIndex(notesIndex) {
  const [people, projects, proposals, timeline] = await Promise.all([
    readJson("people.json"),
    readJson("project_rollups.json"),
    readJson("proposals_archive.json"),
    readJson("timeline_events.json"),
  ]);

  const records = [
    {
      title: "Economic Map",
      href: "/network/",
      kind: "Map",
      summary: "Treasury, proposals, projects, and people rendered as one public graph.",
    },
    {
      title: "Treasury Flows",
      href: "/treasury/",
      kind: "Treasury",
      summary: "Proposal-to-project-to-recipient routing through the Gnars treasury.",
    },
  ];

  for (const person of people.records) {
    records.push({
      title: person.display_name,
      href: `/community/${person.slug}/`,
      kind: "Community",
      summary: stripMarkdown(person.bio || person.role || person.address_short),
    });
  }

  for (const project of projects.records) {
    records.push({
      title: project.name,
      href: `/projects/${project.project_id}/`,
      kind: "Project",
      summary: stripMarkdown(project.objective),
    });
  }

  for (const proposal of proposals.records) {
    const numberLabel = proposal.proposal_number !== null ? `Prop #${proposal.proposal_number}` : proposal.archive_id;
    records.push({
      title: `${numberLabel} - ${proposal.title}`,
      href: `/proposals/${proposal.archive_id}/`,
      kind: "Proposal",
      summary: stripMarkdown(proposal.content_summary),
    });
  }

  for (const event of timeline.records.slice(0, 240)) {
    records.push({
      title: event.title,
      href: event.archive_id
        ? `/proposals/${event.archive_id}/`
        : event.project_id
          ? `/projects/${event.project_id}/`
          : "/timeline/",
      kind: "Timeline",
      summary: stripMarkdown(event.summary),
    });
  }

  for (const note of notesIndex.records) {
    records.push({
      title: note.title,
      href: note.href,
      kind: "Archive",
      summary: note.excerpt,
    });
  }

  return {
    dataset: "search_index",
    as_of: new Date().toISOString(),
    version: 1,
    records,
  };
}

async function main() {
  await fs.rm(publicDataDir, { recursive: true, force: true });
  await fs.mkdir(publicDataDir, { recursive: true });

  const entries = await fs.readdir(dataDir, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isFile() || !entry.name.endsWith(".json")) {
      continue;
    }
    await fs.copyFile(path.join(dataDir, entry.name), path.join(publicDataDir, entry.name));
  }

  const [notesIndex, networkGraph, treasuryFlows, activityTimeseries] = await Promise.all([
    buildNotesIndex(),
    readJson("network_graph.json"),
    readJson("treasury_flows.json"),
    readJson("activity_timeseries.json"),
  ]);

  const searchIndex = await buildSearchIndex(notesIndex);
  const networkView = buildNetworkView(networkGraph);
  const treasuryView = buildTreasuryView(treasuryFlows);
  const activityView = buildActivityView(activityTimeseries);

  await fs.writeFile(path.join(publicDataDir, "notes_index.json"), JSON.stringify(notesIndex, null, 2));
  await fs.writeFile(path.join(publicDataDir, "search-index.json"), JSON.stringify(searchIndex, null, 2));
  await fs.writeFile(path.join(publicDataDir, "network_view.json"), JSON.stringify(networkView, null, 2));
  await fs.writeFile(path.join(publicDataDir, "treasury_view.json"), JSON.stringify(treasuryView, null, 2));
  await fs.writeFile(path.join(publicDataDir, "activity_view.json"), JSON.stringify(activityView, null, 2));

  console.log("[ok] prepared public data payloads");
}

await main();
