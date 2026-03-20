import { formatDate, formatLabel } from "../lib/format";
import type { FeedStreamItem } from "../types";

export function FeedStream({ items }: { items: FeedStreamItem[] }) {
  return (
    <div className="feed-stream">
      {items.map((item) => (
        <a key={item.item_id} className="feed-row" href={item.primary_href}>
          <div className="feed-meta">
            <span>{formatDate(item.date)}</span>
            <span>{item.action_label}</span>
            <span>{formatLabel(item.resolved_status || item.status)}</span>
            {item.chain ? <span>{formatLabel(item.chain)}</span> : null}
          </div>
          <div className="feed-body">
            <strong>{item.title}</strong>
            <p>{item.summary}</p>
            {(item.requested_budget_display || item.routed_budget_display || item.proposer_label) ? (
              <div className="feed-inline-detail">
                {item.proposer_label ? <span>By {item.proposer_label}</span> : null}
                {item.requested_budget_display ? <span>Requested {item.requested_budget_display}</span> : null}
                {item.routed_budget_display && item.routed_budget_display !== item.requested_budget_display ? (
                  <span>Routed {item.routed_budget_display}</span>
                ) : null}
              </div>
            ) : null}
          </div>
          <div className="feed-labels">
            <span className={`tag ${item.reconciliation_status === "needs-review" ? "tag-warn" : "tag-ok"}`}>
              {item.reconciliation_status === "needs-review" ? "Needs Review" : "Matched"}
            </span>
            {item.labels.slice(0, 5).map((label) => (
              <span key={`${item.item_id}:${label}`} className="tag">
                {label}
              </span>
            ))}
          </div>
        </a>
      ))}
    </div>
  );
}
