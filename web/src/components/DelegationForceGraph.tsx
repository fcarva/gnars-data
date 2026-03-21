import { useMemo } from "react";
import { forceCenter, forceLink, forceManyBody, forceSimulation } from "d3-force";
import type { DelegationGraphData } from "@/lib/gnars-data";

interface DelegationForceGraphProps {
  data: DelegationGraphData | null;
}

type SimNode = {
  id: string;
  total_votes: number;
  x?: number;
  y?: number;
};

type SimLink = {
  source: SimNode;
  target: SimNode;
  weight: number;
};

function safeRadius(value: number): number {
  return Math.max(4, Math.min(18, 4 + Math.sqrt(Math.max(0, value)) * 0.35));
}

export function DelegationForceGraph({ data }: DelegationForceGraphProps) {
  const width = 860;
  const height = 420;

  const layout = useMemo(() => {
    if (!data || !data.nodes.length) {
      return { nodes: [], links: [] };
    }

    const nodes: SimNode[] = data.nodes.slice(0, 80).map((node) => ({
      id: node.id,
      total_votes: node.total_votes,
      x: (node.x + 1) * (width * 0.5),
      y: (node.y + 1) * (height * 0.5),
    }));

    const allowed = new Set(nodes.map((node) => node.id));
    const links: SimLink[] = data.links
      .filter((link) => allowed.has(link.source) && allowed.has(link.target))
      .slice(0, 260)
      .map((link) => ({
        source: link.source,
        target: link.target,
        weight: link.weight,
      }));

    const simulation = forceSimulation(nodes)
      .force("charge", forceManyBody().strength(-120))
      .force("center", forceCenter(width / 2, height / 2))
      .force(
        "link",
        forceLink<SimNode, SimLink>(nodes.length > 1 ? links : [])
          .id((d) => d.id)
          .distance(70)
          .strength(0.3)
      )
      .stop();

    for (let i = 0; i < 300; i += 1) {
      simulation.tick();
    }

    return {
      nodes,
      links,
    };
  }, [data]);

  if (!data || !data.nodes.length) {
    return <div className="analytics-note">No delegation graph data available.</div>;
  }

  return (
    <div className="analytics-delegation-wrap">
      <svg className="analytics-delegation-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Delegation graph">
        {layout.links.map((link, idx) => {
          const source = link.source as SimNode;
          const target = link.target as SimNode;
          return (
            <line
              key={`${source.id}:${target.id}:${idx}`}
              x1={source.x || 0}
              y1={source.y || 0}
              x2={target.x || 0}
              y2={target.y || 0}
              className="analytics-delegation-link"
              strokeWidth={Math.max(0.5, Math.min(2.2, link.weight / 120))}
            />
          );
        })}
        {layout.nodes.map((node) => (
          <g key={node.id} transform={`translate(${node.x || 0}, ${node.y || 0})`}>
            <circle className="analytics-delegation-node" r={safeRadius(node.total_votes)} />
          </g>
        ))}
      </svg>
      <div className="analytics-sankey-meta">
        <span>NODES: {data.overview.node_count}</span>
        <span>EDGES: {data.overview.edge_count}</span>
        <span>DENSITY: {data.overview.density.toFixed(3)}</span>
        <span>LARGEST COMPONENT: {data.overview.largest_component_size}</span>
      </div>
    </div>
  );
}
