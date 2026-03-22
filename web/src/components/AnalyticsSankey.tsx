import { useEffect, useMemo, useState, type MouseEvent } from "react";
import { fmtUSD } from "@/lib/format";
import type { SankeyData } from "@/lib/gnars-data";

interface AnalyticsSankeyProps {
  data: SankeyData | null;
}

type SankeyBand = {
  id: string;
  label: string;
  val: number;
  pct: number;
  col: string;
  rec: string;
};

type SemanticSankey = {
  dataset: string;
  mode: "impact" | "workstream";
  cats: SankeyBand[];
  total_k: number;
};

export function AnalyticsSankey({ data }: AnalyticsSankeyProps) {
  const [impact, setImpact] = useState<SemanticSankey | null>(null);
  const [workstream, setWorkstream] = useState<SemanticSankey | null>(null);
  const [mode, setMode] = useState<"impact" | "workstream">("impact");
  const [hovered, setHovered] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; label: string; val: number; pct: number } | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetch("/data/sankey_impact.json").then((res) => (res.ok ? res.json() : null)),
      fetch("/data/sankey_workstream.json").then((res) => (res.ok ? res.json() : null)),
    ])
      .then(([impactPayload, workstreamPayload]) => {
        if (cancelled) return;
        setImpact(impactPayload);
        setWorkstream(workstreamPayload);
      })
      .catch(() => {
        if (cancelled) return;
        setImpact(null);
        setWorkstream(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const payload = mode === "impact" ? impact : workstream;
  const bands = payload?.cats || [];
  const total = useMemo(() => bands.reduce((sum, row) => sum + row.val, 0), [bands]);

  if (!payload || !bands.length) {
    if (!data || !data.nodes.length || !data.links.length) {
      return <div className="analytics-note">No Sankey data available.</div>;
    }
    return <div className="analytics-note">Semantic Sankey loading...</div>;
  }

  const W = 700;
  const H = 300;
  const BW = 108;
  const GAP = 6;
  const PAD = 16;
  const avH = H - PAD * 2 - GAP * (bands.length - 1);
  let curY = PAD;
  const boxes = bands.map((b) => {
    const h = Math.max(12, total > 0 ? (b.val / total) * avH : 12);
    const row = { ...b, y: curY, h, midY: curY + h / 2 };
    curY += h + GAP;
    return row;
  });
  const c1 = 14;
  const c2 = Math.round(W * 0.37);
  const c3 = Math.round(W * 0.73);
  const srcH = H - PAD * 2;
  let srcCurY = PAD;

  const flows = boxes.flatMap((b) => {
    const sh = total > 0 ? (b.val / total) * srcH : 0;
    const mx1 = (c1 + BW + c2) / 2;
    const mx2 = (c2 + BW + c3) / 2;
    const sourceY0 = srcCurY;
    const sourceY1 = srcCurY + sh;
    srcCurY += sh;
    return [
      {
        id: `f-src-${b.id}`,
        source: "treasury",
        target: `cat:${b.id}`,
        col: b.col,
        path: `M${c1 + BW},${sourceY0} C${mx1},${sourceY0} ${mx1},${b.y} ${c2},${b.y} L${c2},${b.y + b.h} C${mx1},${b.y + b.h} ${mx1},${sourceY1} ${c1 + BW},${sourceY1} Z`,
      },
      {
        id: `f-rec-${b.id}`,
        source: `cat:${b.id}`,
        target: `rec:${b.id}`,
        col: b.col,
        path: `M${c2 + BW},${b.y} C${mx2},${b.y} ${mx2},${b.y} ${c3},${b.y} L${c3},${b.y + b.h} C${mx2},${b.y + b.h} ${mx2},${b.y + b.h} ${c2 + BW},${b.y + b.h} Z`,
      },
    ];
  });

  const selectedConnected = useMemo(() => {
    if (!selected) return new Set<string>();
    const connected = new Set<string>();
    for (const flow of flows) {
      if (flow.source === selected || flow.target === selected) {
        connected.add(flow.source);
        connected.add(flow.target);
      }
    }
    return connected;
  }, [flows, selected]);

  const flowOpacity = (source: string, target: string) => {
    if (selected === null && hovered === null) return 0.22;
    if (selected !== null) {
      if (source === selected || target === selected) return 0.55;
      return 0.05;
    }
    if (hovered !== null) {
      if (source === hovered || target === hovered) return 0.4;
      return 0.12;
    }
    return 0.22;
  };

  const nodeOpacity = (nodeId: string) => {
    if (selected === null) return 1;
    if (nodeId === selected) return 1;
    if (selectedConnected.has(nodeId)) return 1;
    return 0.25;
  };

  const showNodeTooltip = (event: MouseEvent<SVGRectElement>, node: SankeyBand, nodeId: string) => {
    event.stopPropagation();
    setHovered(nodeId);
    setTooltip({ x: event.clientX, y: event.clientY, label: node.label, val: node.val, pct: node.pct });
  };

  const clearNodeTooltip = () => {
    setHovered(null);
    setTooltip(null);
  };

  return (
    <div>
      <div className="analytics-block-title">CAPITAL FLOW SANKEY</div>
      <div style={{ display: "flex", gap: 5, marginBottom: 10 }}>
        <button className={`skt${mode === "impact" ? " on" : ""}`} onClick={() => setMode("impact")}>
          BY IMPACT
        </button>
        <button className={`skt${mode === "workstream" ? " on" : ""}`} onClick={() => setMode("workstream")}>
          BY WORKSTREAM
        </button>
      </div>
      <div className="analytics-sankey-wrap" style={{ position: "relative" }}>
        <svg
          width="100%"
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="xMidYMin meet"
          style={{ display: "block" }}
          onClick={() => setSelected(null)}
        >
          <text x={c1 + BW / 2} y={8} textAnchor="middle" fontSize={7.5} fill="#6F6E69" letterSpacing="0.1em">SOURCE</text>
          <text x={c2 + BW / 2} y={8} textAnchor="middle" fontSize={7.5} fill="#6F6E69" letterSpacing="0.1em">CATEGORY</text>
          <text x={c3 + BW / 2} y={8} textAnchor="middle" fontSize={7.5} fill="#6F6E69" letterSpacing="0.1em">RECIPIENT</text>

          <rect
            x={c1}
            y={PAD}
            width={BW}
            height={srcH}
            fill="#282726"
            rx={2}
            fillOpacity={nodeOpacity("treasury")}
            onMouseEnter={() => setHovered("treasury")}
            onMouseLeave={() => clearNodeTooltip()}
            onClick={(event) => {
              event.stopPropagation();
              setSelected((value) => (value === "treasury" ? null : "treasury"));
            }}
            style={{ cursor: "pointer" }}
          />
          <text x={c1 + BW / 2} y={PAD + srcH / 2 - 8} textAnchor="middle" fontSize={10} fill="#FFFCF0" fontWeight={700}>TREASURY</text>
          <text x={c1 + BW / 2} y={PAD + srcH / 2 + 7} textAnchor="middle" fontSize={9} fill="#B7B5AC">{fmtUSD(payload.total_k * 1000)}</text>

          {flows.map((flow) => (
            <path
              key={flow.id}
              d={flow.path}
              fill={flow.col}
              fillOpacity={flowOpacity(flow.source, flow.target)}
              stroke="none"
            />
          ))}

          {boxes.map((b) => {
            return (
              <g key={b.id}>
                <rect
                  x={c2}
                  y={b.y}
                  width={BW}
                  height={b.h}
                  fill={b.col}
                  fillOpacity={0.13 * nodeOpacity(`cat:${b.id}`)}
                  rx={2}
                  onMouseEnter={(event) => showNodeTooltip(event, b, `cat:${b.id}`)}
                  onMouseLeave={() => clearNodeTooltip()}
                  onClick={(event) => {
                    event.stopPropagation();
                    setSelected((value) => (value === `cat:${b.id}` ? null : `cat:${b.id}`));
                  }}
                  style={{ cursor: "pointer" }}
                />
                <rect x={c2} y={b.y} width={4} height={b.h} fill={b.col} fillOpacity={nodeOpacity(`cat:${b.id}`)} rx={1} />

                {b.h >= 28 ? (
                  <>
                    <text x={c2 + BW / 2 + 3} y={b.midY - 5} textAnchor="middle" fontSize={9} fill={b.col} fontWeight={700}>{b.label}</text>
                    <text x={c2 + BW / 2 + 3} y={b.midY + 7} textAnchor="middle" fontSize={8} fill="#575653">${b.val.toFixed(1)}k · {b.pct}%</text>
                  </>
                ) : b.h >= 16 ? (
                  <text x={c2 + BW / 2 + 3} y={b.midY + 3} textAnchor="middle" fontSize={8.5} fill={b.col}>{b.label}</text>
                ) : (
                  <>
                    <line x1={c2 + BW + 2} y1={b.midY} x2={c2 + BW + 8} y2={b.midY} stroke={b.col} strokeWidth={1} />
                    <text x={c2 + BW + 10} y={b.midY + 3} fontSize={8} fill={b.col}>{b.label}</text>
                  </>
                )}

                <rect
                  x={c3}
                  y={b.y}
                  width={BW}
                  height={b.h}
                  fill={b.col}
                  fillOpacity={0.13 * nodeOpacity(`rec:${b.id}`)}
                  rx={2}
                  onMouseEnter={(event) => showNodeTooltip(event, b, `rec:${b.id}`)}
                  onMouseLeave={() => clearNodeTooltip()}
                  onClick={(event) => {
                    event.stopPropagation();
                    setSelected((value) => (value === `rec:${b.id}` ? null : `rec:${b.id}`));
                  }}
                  style={{ cursor: "pointer" }}
                />
                <rect x={c3 + BW - 4} y={b.y} width={4} height={b.h} fill={b.col} fillOpacity={nodeOpacity(`rec:${b.id}`)} rx={1} />
                {b.h >= 22 ? <text x={c3 + BW / 2} y={b.midY + 3} textAnchor="middle" fontSize={8.5} fill="#282726">{b.rec}</text> : null}
              </g>
            );
          })}
        </svg>

        {tooltip ? (
          <div
            style={{
              position: "fixed",
              left: tooltip.x + 10,
              top: tooltip.y + 10,
              pointerEvents: "none",
              background: "#282726",
              color: "#FFFEF8",
              fontSize: 9,
              fontFamily: "'Courier New', monospace",
              borderRadius: 2,
              padding: "8px 10px",
              zIndex: 30,
            }}
          >
            <div>{tooltip.label}</div>
            <div>{`$${tooltip.val.toFixed(1)}k`}</div>
            <div>{`${tooltip.pct}% of treasury`}</div>
            <div style={{ color: "var(--b500)", marginTop: 4 }}>click to highlight · click again to reset</div>
          </div>
        ) : null}
      </div>
      <div className="analytics-sankey-meta">
        {bands.map((row) => (
          <span key={row.id}>
            <span style={{ display: "inline-block", width: 8, height: 8, background: row.col, borderRadius: 1, marginRight: 5 }} />
            {row.label} · ${row.val}k · {row.pct}%
          </span>
        ))}
      </div>
    </div>
  );
}
