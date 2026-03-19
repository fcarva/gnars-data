import { useMemo, useState } from "react";
import { formatNumber } from "../lib/format";
import type { TreasuryViewData } from "../types";

export function SankeyChart({ view }: { view: TreasuryViewData }) {
  const [activeWindow, setActiveWindow] = useState(view.scenes[0]?.window_id ?? "30d");
  const scene = useMemo(
    () => view.scenes.find((item) => item.window_id === activeWindow) ?? view.scenes[0],
    [activeWindow, view.scenes],
  );

  if (!scene) {
    return null;
  }

  return (
    <section className="graph-card">
      <div className="filter-row tight">
        {view.scenes.map((item) => (
          <button
            key={item.window_id}
            className={item.window_id === activeWindow ? "filter-pill is-active" : "filter-pill"}
            type="button"
            onClick={() => setActiveWindow(item.window_id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <svg className="sankey-chart" viewBox={`0 0 ${scene.width} ${scene.height}`} role="img" aria-label="Treasury routing Sankey">
        {scene.links.map((link) => (
          <path
            key={link.link_id}
            className={`sankey-link asset-${link.asset_symbol.toLowerCase()}`}
            d={link.path}
            strokeWidth={Math.max(1, link.width)}
          />
        ))}
        {scene.nodes.map((node) => (
          <g key={node.id} className={`sankey-node kind-${node.kind}`}>
            <rect x={node.x0} y={node.y0} width={node.x1 - node.x0} height={Math.max(4, node.y1 - node.y0)} rx={4} />
            <text x={node.x1 + 6} y={node.y0 + 12}>
              {node.label}
            </text>
          </g>
        ))}
      </svg>
      <div className="chart-foot">
        <small>{scene.label}</small>
        <small>{formatNumber(scene.route_count)} routed transfers</small>
      </div>
    </section>
  );
}
