import { useMemo, useState } from "react";
import type { Member } from "@/lib/gnars-data";

interface AthletesLeaderboardProps {
  members: Member[];
}

const STRICT_TERMS = ["athlete", "rider"];
const HEURISTIC_TERMS = ["skate", "surf", "bmx", "snow", "shred"];

function strictAthleteMatch(member: Member): boolean {
  const role = (member.role || "").toLowerCase();
  const domains = (member.domains || []).map((value) => value.toLowerCase());
  const roleMatch = STRICT_TERMS.some((term) => role.includes(term));
  const domainMatch = domains.some((domain) => STRICT_TERMS.includes(domain));
  return roleMatch || domainMatch;
}

function heuristicAthleteMatch(member: Member): boolean {
  const role = (member.role || "").toLowerCase();
  const domains = (member.domains || []).join(" ").toLowerCase();
  const notes = (member.notes || "").toLowerCase();
  const haystack = `${role} ${domains} ${notes}`;
  return HEURISTIC_TERMS.some((hint) => haystack.includes(hint));
}

export function AthletesLeaderboard({ members }: AthletesLeaderboardProps) {
  const [query, setQuery] = useState("");

  const entries = useMemo(() => {
    const strictMatches = members.filter(strictAthleteMatch);
    const athletePool = strictMatches.length >= 3 ? strictMatches : members.filter((member) => strictAthleteMatch(member) || heuristicAthleteMatch(member));

    return athletePool
      .map((member) => {
        const totalReceivedUsd = (member.total_received_usdc || 0) + (member.total_received_eth || 0) * 2800;
        const attendancePct = member.metrics?.attendance_pct || 0;
        return {
          member,
          totalReceivedUsd,
          fundedProposalCount: member.funded_proposal_count || 0,
          activeVotes: member.metrics?.active_votes || 0,
          attendancePct,
        };
      })
      .filter((entry) => entry.totalReceivedUsd > 0 || entry.fundedProposalCount > 0)
      .sort((a, b) => {
        if (b.totalReceivedUsd !== a.totalReceivedUsd) return b.totalReceivedUsd - a.totalReceivedUsd;
        if (b.fundedProposalCount !== a.fundedProposalCount) return b.fundedProposalCount - a.fundedProposalCount;
        if (b.attendancePct !== a.attendancePct) return b.attendancePct - a.attendancePct;
        return b.activeVotes - a.activeVotes;
      });
  }, [members]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return entries;
    return entries.filter((entry) => {
      const name = (entry.member.display_name || "").toLowerCase();
      const address = (entry.member.address || "").toLowerCase();
      return name.includes(q) || address.includes(q);
    });
  }, [entries, query]);

  return (
    <div className="analytics-table-wrap">
      <div className="search-row">
        <h4 className="analytics-block-title" style={{ marginBottom: 0 }}>ATHLETES LEADERBOARD</h4>
        <div className="search-wrap">
          <input
            className="lb-search"
            type="search"
            placeholder="Search athletes..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
      </div>

      <div className="analytics-table">
        {filtered.slice(0, 12).map((entry, index) => (
          <div key={entry.member.member_id || entry.member.address} className="analytics-table-row">
            <span className="analytics-table-rank">{index + 1}</span>
            <span className="analytics-table-name">{entry.member.display_name || entry.member.address}</span>
            <span className="analytics-table-value">${entry.totalReceivedUsd.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
          </div>
        ))}
      </div>

      {filtered.length === 0 ? <div className="analytics-note">No athletes matched this search.</div> : null}
    </div>
  );
}
