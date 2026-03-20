import { useEffect, useMemo, useState } from "react";
import { sankey, sankeyJustify, sankeyLinkHorizontal } from "d3-sankey";
import { assetTone, formatAmount, formatAssetSymbol, formatNumber } from "../lib/format";
import type { TreasuryRouteRow } from "../types";

type SankeyChartProps = {
  routes: TreasuryRouteRow[];
  windowLabel: string;
};

type SankeyNodeRow = {
  id: string;
  label: string;
  kind: "treasury" | "proposal" | "project" | "recipient";
  href: string | null;
  secondaryLabel?: string | null;
};

type SankeyLinkRow = {
  source: string;
  target: string;
  value: number;
  asset_symbol: string;
  href: string | null;
};

function compactLabel(value: string, limit = 18): string {
  const clean = String(value || "").trim();
  if (!clean) {
    return "UNKNOWN";
  }
  return clean.length > limit ? `${clean.slice(0, limit - 3)}...` : clean;
}

function buildGraph(routes: TreasuryRouteRow[], mode: "grouped" | "full") {
  const sorted = [...routes].sort((left, right) => right.amount - left.amount || right.eventAt.localeCompare(left.eventAt));
  const proposalTotals = new Map<string, number>();
  const recipientTotals = new Map<string, number>();
  const projectTotals = new Map<string, number>();

  for (const route of sorted) {
    proposalTotals.set(route.proposalHref, (proposalTotals.get(route.proposalHref) ?? 0) + route.amount);
    recipientTotals.set(route.recipientHref ?? route.recipientAddress, (recipientTotals.get(route.recipientHref ?? route.recipientAddress) ?? 0) + route.amount);
    if (route.projectHref && route.projectLabel) {
      projectTotals.set(route.projectHref, (projectTotals.get(route.projectHref) ?? 0) + route.amount);
    }
  }

  const topProposalIds = new Set(
    [...proposalTotals.entries()]
      .sort((left, right) => right[1] - left[1])
      .slice(0, mode === "grouped" ? 8 : 32)
      .map(([key]) => key),
  );
  const topRecipientIds = new Set(
    [...recipientTotals.entries()]
      .sort((left, right) => right[1] - left[1])
      .slice(0, mode === "grouped" ? 10 : 36)
      .map(([key]) => key),
  );
  const topProjectIds = new Set(
    [...projectTotals.entries()]
      .sort((left, right) => right[1] - left[1])
      .slice(0, mode === "grouped" ? 6 : 24)
      .map(([key]) => key),
  );

  const nodes = new Map<string, SankeyNodeRow>();
  const grouped = new Map<string, SankeyLinkRow>();

  const registerNode = (node: SankeyNodeRow) => {
    if (!nodes.has(node.id)) {
      nodes.set(node.id, node);
    }
  };

  const pushLink = (source: string, target: string, value: number, asset: string, href: string | null) => {
    const key = `${source}|${target}|${asset}`;
    const current = grouped.get(key);
    if (current) {
      current.value += value;
      return;
    }
    grouped.set(key, {
      source,
      target,
      value,
      asset_symbol: asset,
      href,
    });
  };

  registerNode({ id: "treasury", label: "TREASURY", kind: "treasury", href: "/treasury/" });

  for (const route of sorted) {
    const proposalKey = topProposalIds.has(route.proposalHref) ? `proposal:${route.proposalHref}` : "proposal:other";
    const recipientKeyBase = route.recipientHref ?? route.recipientAddress;
    const recipientKey = topRecipientIds.has(recipientKeyBase) ? `recipient:${recipientKeyBase}` : "recipient:other";
    const projectKey =
      route.projectHref && route.projectLabel
        ? topProjectIds.has(route.projectHref)
          ? `project:${route.projectHref}`
          : "project:other"
        : null;

    registerNode({
      id: proposalKey,
      label: proposalKey === "proposal:other" ? "OTHER PROPOSALS" : route.proposalNumberLabel,
      kind: "proposal",
      href: proposalKey === "proposal:other" ? null : route.proposalHref,
      secondaryLabel: route.proposalTitle,
    });

    if (projectKey) {
      registerNode({
        id: projectKey,
        label: projectKey === "project:other" ? "OTHER PROJECTS" : compactLabel(route.projectLabel ?? "PROJECT"),
        kind: "project",
        href: projectKey === "project:other" ? null : route.projectHref,
        secondaryLabel: route.projectLabel,
      });
    }

    registerNode({
      id: recipientKey,
      label: recipientKey === "recipient:other" ? "OTHER RECIPIENTS" : compactLabel(route.recipientLabel, 20),
      kind: "recipient",
      href: recipientKey === "recipient:other" ? null : route.recipientHref,
      secondaryLabel: recipientKey === "recipient:other" ? null : route.recipientSecondaryLabel,
    });

    pushLink("treasury", proposalKey, route.amount, route.assetSymbol, route.proposalHref);
    if (projectKey) {
      pushLink(proposalKey, projectKey, route.amount, route.assetSymbol, route.projectHref);
      pushLink(projectKey, recipientKey, route.amount, route.assetSymbol, route.recipientHref);
    } else {
      pushLink(proposalKey, recipientKey, route.amount, route.assetSymbol, route.recipientHref);
    }
  }

  const nodeCount = nodes.size;
  const width = 1080;
  const height = Math.max(320, Math.min(680, 120 + nodeCount * 20));
  const graph = sankey<SankeyNodeRow, SankeyLinkRow>()
    .nodeId((node) => node.id)
    .nodeWidth(14)
    .nodePadding(mode === "grouped" ? 16 : 12)
    .nodeAlign(sankeyJustify)
    .nodeSort((left, right) => (right.value ?? 0) - (left.value ?? 0))
    .linkSort((left, right) => (right.value ?? 0) - (left.value ?? 0))
    .extent([
      [12, 12],
      [width - 12, height - 12],
    ])({
      nodes: [...nodes.values()].map((node) => ({ ...node })),
      links: [...grouped.values()].map((link) => ({ ...link })),
    });

  const pathBuilder = sankeyLinkHorizontal();
  const nodeId = (value: string | { id: string }) => (typeof value === "string" ? value : value.id);
  return {
    width,
    height,
    mode,
    totalValue: sorted.reduce((total, route) => total + route.amount, 0),
    routeCount: routes.length,
    visibleNodeCount: graph.nodes.length,
    visibleLinkCount: graph.links.length,
    nodes: graph.nodes,
    links: graph.links.map((link, index) => ({
      link_id: `${mode}:${index}`,
      path: pathBuilder(link),
      source: nodeId(link.source),
      target: nodeId(link.target),
      value: Number(link.value ?? 0),
      width: Number(link.width ?? 0),
      asset_symbol: link.asset_symbol,
      href: link.href,
    })),
  };
}

export function SankeyChart({ routes, windowLabel }: SankeyChartProps) {
  const dense = routes.length > 20;
  const allowFull = routes.length <= 28;
  const [mode, setMode] = useState<"grouped" | "full">(dense || !allowFull ? "grouped" : "full");
  const [activeId, setActiveId] = useState<string | null>(null);
  const uniqueAssets = [...new Set(routes.map((route) => route.assetSymbol))];
  const singleAsset = uniqueAssets.length === 1 ? uniqueAssets[0] : null;
  const singleAssetRoute = singleAsset ? routes.find((route) => route.assetSymbol === singleAsset) ?? null : null;
  const legendAssets = useMemo(
    () =>
      [...new Map(routes.map((route) => [route.assetSymbol, route])).values()].map((route) => ({
        key: route.assetSymbol,
        label: route.assetDisplaySymbol || formatAssetSymbol(route.assetSymbol, route.tokenContract),
        tone: route.assetTone || assetTone(route.assetSymbol),
      })),
    [routes],
  );

  useEffect(() => {
    setMode(routes.length > 20 || routes.length > 28 ? "grouped" : "full");
    setActiveId(null);
  }, [routes.length]);

  const scene = useMemo(() => buildGraph(routes, mode), [mode, routes]);

  if (!routes.length) {
    return (
      <section className="graph-card treasury-flow-card">
        <div className="chart-head">
          <span>{windowLabel}</span>
          <strong>No decoded routed transfers</strong>
        </div>
        <div className="chart-empty">
          <strong>No decoded routed transfers in this window.</strong>
          <span>Try a broader time window or clear asset/category filters.</span>
        </div>
      </section>
    );
  }

  const relatedLinkIds = new Set<string>();
  const relatedNodeIds = new Set<string>();
  if (activeId) {
    for (const link of scene.links) {
      if (link.link_id === activeId || link.source === activeId || link.target === activeId) {
        relatedLinkIds.add(link.link_id);
        relatedNodeIds.add(link.source);
        relatedNodeIds.add(link.target);
      }
    }
  }

  return (
    <section className="graph-card treasury-flow-card">
      <div className="chart-head">
        <span>{windowLabel}</span>
        <strong>
          {singleAsset && singleAssetRoute
            ? formatAmount(singleAsset, scene.totalValue, singleAssetRoute.tokenContract)
            : `${uniqueAssets.length} asset lanes / ${formatNumber(scene.routeCount)} routes`}
        </strong>
      </div>
      <div className="chart-toolbar">
        <div className="filter-row tight">
          <button type="button" className={mode === "grouped" ? "filter-pill is-active" : "filter-pill"} onClick={() => setMode("grouped")}>
            Grouped
          </button>
          <button
            type="button"
            className={mode === "full" ? "filter-pill is-active" : "filter-pill"}
            onClick={() => setMode("full")}
            disabled={!allowFull}
            title={!allowFull ? "Narrow the filter state to inspect the full route topology." : undefined}
          >
            Full
          </button>
        </div>
        <div className="chart-legend treasury-legend">
          {legendAssets.slice(0, 6).map((asset) => (
            <span key={asset.key} className={asset.tone}>
              {asset.label}
            </span>
          ))}
        </div>
      </div>
      <svg className="sankey-chart treasury-sankey" viewBox={`0 0 ${scene.width} ${scene.height}`} role="img" aria-label="Treasury routing Sankey">
        {scene.links.map((link) => {
          const dimmed = activeId ? !relatedLinkIds.has(link.link_id) : false;
          return (
            <path
              key={link.link_id}
              className={`sankey-link asset-${assetTone(link.asset_symbol)} ${dimmed ? "is-dimmed" : ""}`}
              d={link.path ?? ""}
              strokeWidth={Math.max(1, link.width)}
              onMouseEnter={() => setActiveId(link.link_id)}
              onMouseLeave={() => setActiveId(null)}
            />
          );
        })}
        {scene.nodes.map((node) => {
          const dimmed = activeId ? !relatedNodeIds.has(node.id) && node.id !== activeId : false;
          const labelX = (node.x0 ?? 0) < scene.width * 0.5 ? (node.x1 ?? 0) + 6 : (node.x0 ?? 0) - 6;
          const textAnchor = (node.x0 ?? 0) < scene.width * 0.5 ? "start" : "end";
          return (
            <g
              key={node.id}
              className={`sankey-node kind-${node.kind} ${dimmed ? "is-dimmed" : ""}`}
              onMouseEnter={() => setActiveId(node.id)}
              onMouseLeave={() => setActiveId(null)}
            >
              <rect x={node.x0} y={node.y0} width={(node.x1 ?? 0) - (node.x0 ?? 0)} height={Math.max(4, (node.y1 ?? 0) - (node.y0 ?? 0))} rx={2} />
              <text x={labelX} y={(node.y0 ?? 0) + 12} textAnchor={textAnchor}>
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="chart-foot">
        <small>
          {formatNumber(scene.routeCount)} routes / {formatNumber(scene.visibleNodeCount)} nodes / {formatNumber(scene.visibleLinkCount)} links
        </small>
        <small>
          {mode === "grouped"
            ? "Grouped for readability and scale."
            : allowFull
              ? "Full topology for the selected filter state."
              : "Full mode unlocks only on narrower filter states."}
        </small>
      </div>
    </section>
  );
}
