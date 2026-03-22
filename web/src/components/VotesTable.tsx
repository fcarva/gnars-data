import type { FundingAnalysis, TimelineEvent } from "@/lib/gnars-data";

interface VotesTableProps {
  events: TimelineEvent[];
  funding: FundingAnalysis | null;
}

function parseVoteCount(summary: string): number | null {
  const match = summary.match(/(\d+)\s+votes?/i);
  if (!match) return null;
  const parsed = Number.parseInt(match[1], 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function parseVotingPower(summary: string): string {
  const parts = summary.split("voting power");
  if (parts.length < 2) return "-";
  return parts[1].trim();
}

function voteBadge(status: string): string {
  const value = status.toLowerCase();
  if (value === "executed") return "EXECUTED";
  if (value === "active") return "ACTIVE";
  if (value === "succeeded") return "PASSED";
  if (value === "defeated") return "DEFEATED";
  if (value === "cancelled" || value === "canceled") return "CANCELLED";
  return status.toUpperCase();
}

function fmtUsd(value: number | null | undefined): string {
  if (typeof value !== "number") return "-";
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

export function VotesTable({ events, funding }: VotesTableProps) {
  const spendByArchive = new Map(
    (funding?.allocation_by_proposal || []).map((row) => [row.archive_id, row.cost_per_vote_usd]),
  );

  return (
    <section className="section-block">
      <div className="ledger-table compact-ledger">
        <div className="ledger-head">
          <span>Proposal</span>
          <span>Status</span>
          <span>Votes</span>
          <span>Voting Power</span>
          <span>Cost / Vote</span>
        </div>
        <div className="ledger-body">
          {events.map((event) => {
            const voteCount = parseVoteCount(event.summary || "");
            const costPerVote = event.archive_id ? spendByArchive.get(event.archive_id) : null;
            const link = event.links?.[0];
            return (
              <div key={event.event_id} className="ledger-row">
                <span className="ledger-cell ledger-primary">
                  {link ? <a href={link}>{event.title}</a> : <strong>{event.title}</strong>}
                  <small>{event.date.slice(0, 10)}</small>
                </span>
                <span className="ledger-cell ledger-primary">
                  <strong>{voteBadge(event.status)}</strong>
                  <small>{event.proposal_number ? `#${event.proposal_number}` : "proposal"}</small>
                </span>
                <span className="ledger-cell ledger-mono">{voteCount ?? "-"}</span>
                <span className="ledger-cell ledger-mono">{parseVotingPower(event.summary || "")}</span>
                <span className="ledger-cell ledger-mono">{fmtUsd(costPerVote)}</span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
