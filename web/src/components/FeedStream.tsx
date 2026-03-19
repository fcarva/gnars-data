import { formatDate, formatLabel } from "../lib/format";
import type { FeedStreamItem } from "../types";

export function FeedStream({ items }: { items: FeedStreamItem[] }) {
  return (
    <div className="feed-stream">
      {items.map((item) => (
        <a key={item.item_id} className="feed-row" href={item.primary_href}>
          <div className="feed-meta">
            <span>{formatDate(item.date)}</span>
            <span>{formatLabel(item.kind)}</span>
            <span>{formatLabel(item.status)}</span>
          </div>
          <div className="feed-body">
            <strong>{item.title}</strong>
            <p>{item.summary}</p>
          </div>
          <div className="feed-labels">
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
