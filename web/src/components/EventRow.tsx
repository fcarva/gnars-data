import type { TimelineEvent } from "@/lib/gnars-data";
import { relativeTime, shortenAddress } from "@/lib/gnars-data";

const kindLabelMap: Record<string, { label: string; className: string }> = {
  proposal: { label: "PROP", className: "event-label-proposal" },
  vote: { label: "VOTE", className: "event-label-vote" },
  treasury: { label: "TREASURY", className: "event-label-treasury" },
  transfer: { label: "XFER", className: "event-label-transfer" },
  payout: { label: "PAYOUT", className: "event-label-treasury" },
  milestone: { label: "MILESTONE", className: "event-label-milestone" },
  delivery: { label: "DELIVERY", className: "event-label-delivery" },
};

const statusLabelMap: Record<string, { label: string; className: string }> = {
  active: { label: "ACTIVE", className: "event-label-active" },
  defeated: { label: "DEFEATED", className: "event-label-defeated" },
  executed: { label: "EXECUTED", className: "event-label-executed" },
  cancelled: { label: "CANCELLED", className: "event-label-cancelled" },
  succeeded: { label: "PASSED", className: "event-label-succeeded" },
  closed: { label: "CLOSED", className: "event-label-cancelled" },
};

interface EventRowProps {
  event: TimelineEvent;
}

export function EventRow({ event }: EventRowProps) {
  const kindInfo = kindLabelMap[event.kind] || {
    label: event.kind.toUpperCase(),
    className: "feed-row-kind-fallback",
  };
  const statusInfo = statusLabelMap[event.status];
  const time = relativeTime(event.date);
  const link = event.links?.[0];
  const proposer = event.people_addresses?.[0];

  return (
    <div className="feed-row">
      <span className="feed-row-time">{time}</span>
      <span className={`feed-row-kind ${kindInfo.className}`}>{statusInfo ? statusInfo.label : kindInfo.label}</span>

      <div className="feed-row-content">
        <span className="feed-row-title">{event.title}</span>
        {proposer && <span className="feed-row-meta">by {shortenAddress(proposer)}</span>}
        {event.summary && (
          <span className="feed-row-summary">
            "{event.summary.slice(0, 80)}{event.summary.length > 80 ? "..." : ""}"
          </span>
        )}
      </div>

      {link && (
        <a href={link} target="_blank" rel="noopener noreferrer" className="feed-row-link" title={link}>
          ↗
        </a>
      )}
    </div>
  );
}
