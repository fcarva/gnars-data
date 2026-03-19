import { useMemo, useState } from "react";
import type { NetworkViewData, NetworkViewEdge, NetworkViewNode } from "../types";

function nodeMatches(node: NetworkViewNode, tribe: string, status: string) {
  const tribeOk = tribe === "All" || (node.tags ?? []).includes(tribe.toLowerCase());
  const statusOk = status === "All" || node.status === status.toLowerCase();
  return tribeOk && statusOk;
}

function edgeMatches(edge: NetworkViewEdge, asset: string) {
  return asset === "All" || edge.asset_symbol === asset;
}

export function NetworkMap({
  scene,
  mode = "full",
}: {
  scene: NetworkViewData;
  mode?: "home" | "full";
}) {
  const [tribe, setTribe] = useState("All");
  const [asset, setAsset] = useState("All");
  const [status, setStatus] = useState("All");

  const graph = useMemo(() => {
    const baseNodeIds =
      mode === "home" ? new Set(scene.homepage.node_ids) : new Set(scene.nodes.map((node) => node.node_id));
    const candidateNodes = scene.nodes.filter((node) => baseNodeIds.has(node.node_id) && nodeMatches(node, tribe, status));
    const allowedNodeIds = new Set(candidateNodes.map((node) => node.node_id));
    const edges = scene.edges.filter(
      (edge) =>
        allowedNodeIds.has(edge.source) &&
        allowedNodeIds.has(edge.target) &&
        edgeMatches(edge, asset),
    );
    const visibleNodeIds = new Set(edges.flatMap((edge) => [edge.source, edge.target]));
    const nodes = candidateNodes.filter((node) => visibleNodeIds.has(node.node_id));
    return { nodes, edges };
  }, [asset, mode, scene, status, tribe]);

  return (
    <section className="graph-card">
      {mode === "full" ? (
        <div className="filter-row tight">
          {["All", ...scene.filters.tribes.map((item) => item.charAt(0).toUpperCase() + item.slice(1))].map((item) => (
            <button key={item} className={item === tribe ? "filter-pill is-active" : "filter-pill"} type="button" onClick={() => setTribe(item)}>
              {item}
            </button>
          ))}
          {["All", ...scene.filters.assets].map((item) => (
            <button key={item} className={item === asset ? "filter-pill is-active" : "filter-pill"} type="button" onClick={() => setAsset(item)}>
              {item}
            </button>
          ))}
          {["All", ...scene.filters.statuses.map((item) => item.charAt(0).toUpperCase() + item.slice(1))].map((item) => (
            <button key={item} className={item === status ? "filter-pill is-active" : "filter-pill"} type="button" onClick={() => setStatus(item)}>
              {item}
            </button>
          ))}
        </div>
      ) : null}
      <svg className="network-map" viewBox={`0 0 ${scene.width} ${scene.height}`} role="img" aria-label="Economic map of Gnars">
        {graph.edges.map((edge) => (
          <line
            key={edge.edge_id}
            className={`network-edge kind-${edge.kind} asset-${(edge.asset_symbol ?? "none").toLowerCase()}`}
            x1={edge.sourceNode.x}
            y1={edge.sourceNode.y}
            x2={edge.targetNode.x}
            y2={edge.targetNode.y}
            strokeWidth={Math.max(1, Math.min(8, Number(edge.weight ?? 1) * 0.08 + 1))}
          />
        ))}
        {graph.nodes.map((node) => (
          <g key={node.node_id} className={`network-node kind-${node.kind}`}>
            <a href={node.href}>
              {node.kind === "treasury" || node.kind === "project" ? (
                <rect
                  x={node.x - node.radius}
                  y={node.y - node.radius}
                  width={node.radius * 2}
                  height={node.radius * 2}
                  rx={node.kind === "treasury" ? 3 : 8}
                />
              ) : (
                <circle cx={node.x} cy={node.y} r={node.radius} />
              )}
            </a>
            {node.radius >= 9 || mode === "home" ? (
              <text x={node.x + node.radius + 5} y={node.y + 4}>
                {node.kind === "proposal" && node.proposal_number ? `#${node.proposal_number}` : node.label}
              </text>
            ) : null}
          </g>
        ))}
      </svg>
    </section>
  );
}
