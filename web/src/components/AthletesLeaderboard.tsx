import { useMemo, useState } from "react";
import type { Member } from "@/lib/gnars-data";

interface AthletesLeaderboardProps {
  members: Member[];
}

export function AthletesLeaderboard({ members }: AthletesLeaderboardProps) {
  const [query, setQuery] = useState("");
  const [sportFilter, setSportFilter] = useState<"all" | "sk8" | "surf" | "bmx" | "builder">("all");

  const inferSport = (member: Member): "sk8" | "surf" | "bmx" | "builder" | "multi" => {
    const role = (member.role || "").toLowerCase();
    const domains = (member.domains || []).join(" ").toLowerCase();
    const notes = (member.notes || "").toLowerCase();
    const text = `${role} ${domains} ${notes}`;
    if (text.includes("builder") || text.includes("dev") || text.includes("infra")) return "builder";
    if (text.includes("surf")) return "surf";
    if (text.includes("bmx")) return "bmx";
    if (text.includes("skate") || text.includes("sk8")) return "sk8";
    return "multi";
  };

  const entries = useMemo(() => {
    return members
      .map((member) => {
        const totalReceivedUsd = (member.total_received_usdc || 0) + (member.total_received_eth || 0) * 2800;
        const attendancePct = member.metrics?.attendance_pct || 0;
        return {
          member,
          sport: inferSport(member),
          totalReceivedUsd,
          usdc: member.total_received_usdc || 0,
          eth: member.total_received_eth || 0,
          fundedProposalCount: member.funded_proposal_count || 0,
          activeVotes: member.metrics?.active_votes || 0,
          proof: member.metrics?.votes_count || 0,
          attendancePct,
        };
      })
      .sort((a, b) => {
        if (b.totalReceivedUsd !== a.totalReceivedUsd) return b.totalReceivedUsd - a.totalReceivedUsd;
        if (b.proof !== a.proof) return b.proof - a.proof;
        if (b.fundedProposalCount !== a.fundedProposalCount) return b.fundedProposalCount - a.fundedProposalCount;
        if (b.attendancePct !== a.attendancePct) return b.attendancePct - a.attendancePct;
        return b.activeVotes - a.activeVotes;
      });
  }, [members]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let rows = entries;
    if (sportFilter !== "all") {
      rows = rows.filter((entry) => entry.sport === sportFilter);
    }
    if (!q) return rows;
    return rows.filter((entry) => {
      const name = (entry.member.display_name || "").toLowerCase();
      const address = (entry.member.address || "").toLowerCase();
      const role = (entry.member.role || "").toLowerCase();
      return name.includes(q) || address.includes(q) || role.includes(q) || entry.sport.includes(q);
    });
  }, [entries, query, sportFilter]);

  const maxUsdc = Math.max(1, ...filtered.map((entry) => entry.usdc));
  const pillClass = (sport: string) => {
    if (sport === "sk8") return "p-sk";
    if (sport === "surf") return "p-su";
    if (sport === "bmx") return "p-bm";
    if (sport === "builder") return "p-bu";
    return "p-mx";
  };

  return (
    <div>
      <div className="search-row">
        <div className="search-wrap">
          <input
            className="lb-search"
            type="search"
            placeholder="Search..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
        <div className="filter-pills">
          <button className={`fp${sportFilter === "all" ? " on" : ""}`} onClick={() => setSportFilter("all")}>ALL</button>
          <button className={`fp${sportFilter === "sk8" ? " on" : ""}`} onClick={() => setSportFilter("sk8")}>SK8</button>
          <button className={`fp${sportFilter === "surf" ? " on" : ""}`} onClick={() => setSportFilter("surf")}>SURF</button>
          <button className={`fp${sportFilter === "bmx" ? " on" : ""}`} onClick={() => setSportFilter("bmx")}>BMX</button>
          <button className={`fp${sportFilter === "builder" ? " on" : ""}`} onClick={() => setSportFilter("builder")}>BUILDERS</button>
        </div>
        <span className="pg">{filtered.length} rows</span>
      </div>

      <div className="lb-wrap">
        <table className="lb">
          <thead>
            <tr>
              <th>#</th>
              <th>MEMBER</th>
              <th>ROLE</th>
              <th className="r">SPORT</th>
              <th className="r">USDC</th>
              <th className="r">ETH</th>
              <th className="r">PROPS</th>
              <th className="r">PROOF</th>
              <th className="r">SHARE</th>
            </tr>
          </thead>
          <tbody>
            {filtered.slice(0, 24).map((entry, index) => {
              const share = entry.usdc > 0 ? Math.round((entry.usdc / maxUsdc) * 100) : 0;
              return (
                <tr key={entry.member.member_id || entry.member.address}>
                  <td><span className="rank">{index + 1}</span></td>
                  <td>{entry.member.display_name || entry.member.address}</td>
                  <td>{entry.member.role || "-"}</td>
                  <td className="num"><span className={`pill ${pillClass(entry.sport)}`}>{entry.sport.toUpperCase()}</span></td>
                  <td className="num">{entry.usdc > 0 ? entry.usdc.toLocaleString() : "-"}</td>
                  <td className="num">{entry.eth > 0 ? entry.eth.toFixed(2) : "-"}</td>
                  <td className="num">{entry.fundedProposalCount}</td>
                  <td className="num">{entry.proof}</td>
                  <td className="num">
                    {share > 0 ? (
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                        <span className="bar-bg" style={{ width: 48 }}><span className="bar-fg" style={{ width: `${share}%`, background: "#3AA99F", display: "block" }} /></span>
                        {share}%
                      </span>
                    ) : "-"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 ? <div className="analytics-note">No rows matched your filters.</div> : null}
    </div>
  );
}
