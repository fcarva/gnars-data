import { useEffect, useMemo, useState } from "react";
import { fmtETH, fmtUSDFull } from "@/lib/format";

type SportFundingRow = {
  sport: string;
  pill: string;
  label: string;
  color: string;
  athletes: number;
  proposals: number;
  usdc: number;
  eth: number;
  usd_equiv: number;
  pct: number;
  top_recipient: string;
};

type SportFundingPayload = {
  dataset: string;
  rows: SportFundingRow[];
  total_usd: number;
};

const PILL_CLASS: Record<string, string> = {
  sk8: "p-sk",
  surf: "p-su",
  bmx: "p-bm",
  snow: "p-sn",
  multi: "p-mx",
};

function SkeletonRows() {
  return (
    <tbody>
      {Array.from({ length: 3 }).map((_, index) => (
        <tr key={`skeleton-${index}`}>
          <td><div style={{ width: 120, height: 16, background: "#F2F0E5", borderRadius: 4 }} /></td>
          <td><div style={{ width: 28, height: 14, background: "#F2F0E5", borderRadius: 4, marginLeft: "auto" }} /></td>
          <td><div style={{ width: 28, height: 14, background: "#F2F0E5", borderRadius: 4, marginLeft: "auto" }} /></td>
          <td><div style={{ width: 72, height: 14, background: "#F2F0E5", borderRadius: 4, marginLeft: "auto" }} /></td>
          <td><div style={{ width: 50, height: 14, background: "#F2F0E5", borderRadius: 4, marginLeft: "auto" }} /></td>
          <td><div style={{ width: 90, height: 6, background: "#F2F0E5", borderRadius: 4, marginLeft: "auto" }} /></td>
          <td><div style={{ width: 110, height: 14, background: "#F2F0E5", borderRadius: 4 }} /></td>
        </tr>
      ))}
    </tbody>
  );
}

export function SportFundingTable() {
  const [payload, setPayload] = useState<SportFundingPayload | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/data/sport_funding.json")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!cancelled) setPayload(data);
      })
      .catch(() => {
        if (!cancelled) setPayload(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const rows = useMemo(() => {
    const list = payload?.rows || [];
    return [...list].sort((a, b) => b.usd_equiv - a.usd_equiv);
  }, [payload]);

  const totals = useMemo(() => {
    const base = {
      athletes: 0,
      proposals: 0,
      usdc: 0,
      eth: 0,
    };
    for (const row of rows) {
      base.athletes += row.athletes;
      base.proposals += row.proposals;
      base.usdc += row.usdc;
      base.eth += row.eth;
    }
    return base;
  }, [rows]);

  return (
    <div>
      <div className="analytics-block-title">ATHLETES — CAPITAL BY SPORT</div>
      <table className="at" style={{ width: "100%" }}>
        <thead>
          <tr>
            <th>SPORT</th>
            <th style={{ textAlign: "right" }}>ATHLETES</th>
            <th style={{ textAlign: "right" }}>PROPOSALS</th>
            <th style={{ textAlign: "right" }}>USDC</th>
            <th style={{ textAlign: "right" }}>ETH</th>
            <th style={{ textAlign: "right" }}>% OF ATHLETE SPEND</th>
            <th>TOP RECIPIENT</th>
          </tr>
        </thead>
        {!payload || !rows.length ? (
          <SkeletonRows />
        ) : (
          <>
            <tbody>
              {rows.map((row) => (
                <tr key={row.sport}>
                  <td>
                    <span className={`pill ${PILL_CLASS[row.sport] || "p-mx"}`}>{row.pill || row.sport.toUpperCase()}</span>
                    <span style={{ marginLeft: 8 }}>{row.label}</span>
                  </td>
                  <td style={{ textAlign: "right", fontFamily: "var(--mono)" }}>{row.athletes}</td>
                  <td style={{ textAlign: "right", fontFamily: "var(--mono)" }}>{row.proposals}</td>
                  <td style={{ textAlign: "right", fontFamily: "var(--mono)" }}>{fmtUSDFull(row.usdc)}</td>
                  <td style={{ textAlign: "right", fontFamily: "var(--mono)" }}>{fmtETH(row.eth)}</td>
                  <td style={{ textAlign: "right" }}>
                    <div style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                      <div className="bar-bg" style={{ width: 60, height: 4 }}>
                        <div className="bar-fg" style={{ width: `${Math.min(100, row.pct)}%`, background: row.color }} />
                      </div>
                      <span style={{ fontSize: 9, color: "#6F6E69", minWidth: 24 }}>{row.pct}%</span>
                    </div>
                  </td>
                  <td style={{ fontSize: 10, color: "#403E3C" }}>{row.top_recipient || "—"}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td style={{ fontWeight: 700, borderTop: "1px solid #E6E4D9" }}>TOTAL ATHLETES</td>
                <td style={{ textAlign: "right", fontFamily: "var(--mono)", fontWeight: 700, borderTop: "1px solid #E6E4D9" }}>{totals.athletes}</td>
                <td style={{ textAlign: "right", fontFamily: "var(--mono)", fontWeight: 700, borderTop: "1px solid #E6E4D9" }}>{totals.proposals}</td>
                <td style={{ textAlign: "right", fontFamily: "var(--mono)", fontWeight: 700, borderTop: "1px solid #E6E4D9" }}>{fmtUSDFull(totals.usdc)}</td>
                <td style={{ textAlign: "right", fontFamily: "var(--mono)", fontWeight: 700, borderTop: "1px solid #E6E4D9" }}>{fmtETH(totals.eth)}</td>
                <td style={{ borderTop: "1px solid #E6E4D9" }} />
                <td style={{ borderTop: "1px solid #E6E4D9" }} />
              </tr>
            </tfoot>
          </>
        )}
      </table>
    </div>
  );
}
