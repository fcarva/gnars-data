import { ResponsiveContainer, Sankey, Tooltip } from "recharts";
import type { SankeyData } from "@/lib/gnars-data";

interface AnalyticsSankeyProps {
  data: SankeyData | null;
}

export function AnalyticsSankey({ data }: AnalyticsSankeyProps) {
  const sankey = data;
  if (!sankey || !sankey.nodes.length || !sankey.links.length) {
    return <div className="analytics-note">No Sankey data available.</div>;
  }

  const chartData = {
    nodes: sankey.nodes.map((node) => ({ name: node.label })),
    links: sankey.links,
  };

  return (
    <div>
      <div className="analytics-block-title">CAPITAL FLOW SANKEY</div>
      <div className="analytics-sankey-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <Sankey
            data={chartData}
            nodePadding={22}
            nodeWidth={12}
            margin={{ top: 10, right: 10, bottom: 10, left: 10 }}
            iterations={64}
            link={{ stroke: "rgba(67, 133, 190, 0.35)" }}
            node={{ stroke: "rgba(64, 62, 60, 0.8)", fill: "rgba(67, 133, 190, 0.75)" }}
          >
            <Tooltip
              formatter={(value) => {
                const n = typeof value === "number" ? value : Number(value ?? 0);
                return [`$${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}`, "Flow"];
              }}
              contentStyle={{
                border: "1px solid rgba(64, 62, 60, 0.8)",
                borderRadius: 8,
                background: "rgba(16, 15, 15, 0.95)",
                color: "#cecdc3",
              }}
            />
          </Sankey>
        </ResponsiveContainer>
      </div>
      <div className="analytics-sankey-meta">
        <span>Track: {sankey.track}</span>
        {sankey.decoding ? (
          <span>
            decoded {sankey.decoding.matched_routes} / unmatched {sankey.decoding.unmatched_routes}
          </span>
        ) : null}
      </div>
    </div>
  );
}
