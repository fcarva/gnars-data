import { formatLabel } from "../lib/format";
import type { TimelineCard } from "../types";

export function TimelineFeed({ items }: { items: TimelineCard[] }) {
  return (
    <div className="timeline-feed">
      {items.map((item) => (
        <article key={item.eventId} className="timeline-card">
          <div className="timeline-meta">
            <span>{item.dateLabel}</span>
            <span>{formatLabel(item.kind)}</span>
            <span>{formatLabel(item.status)}</span>
          </div>
          <h3>{item.title}</h3>
          <p>{item.summary}</p>
          <div className="timeline-links">
            {item.project ? <a href={item.project.href}>{item.project.label}</a> : null}
            {item.people.map((person) => (
              <a key={person.href} href={person.href}>
                {person.label}
              </a>
            ))}
            {item.href ? <a href={item.href}>Open</a> : null}
          </div>
        </article>
      ))}
    </div>
  );
}
