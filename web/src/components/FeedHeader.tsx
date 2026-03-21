import type { EventFilter } from "@/lib/gnars-data";

const tabs: { label: string; value: EventFilter }[] = [
  { label: "ALL", value: "all" },
  { label: "PROPOSALS", value: "proposals" },
  { label: "VOTES", value: "votes" },
  { label: "TREASURY", value: "treasury" },
  { label: "MILESTONES", value: "milestones" },
  { label: "DELIVERIES", value: "deliveries" },
  { label: "ANALYTICS", value: "analytics" },
];

interface FeedHeaderProps {
  activeFilter: EventFilter;
  onFilterChange: (filter: EventFilter) => void;
}

export function FeedHeader({ activeFilter, onFilterChange }: FeedHeaderProps) {
  return (
    <header className="feed-header">
      <div className="feed-header-inner">
        <div className="feed-header-top">
          <a href="/" className="feed-brand">
            GNARS.DATA
          </a>
          <a
            href="https://github.com/fcarva/gnars-data"
            target="_blank"
            rel="noopener noreferrer"
            className="feed-header-link"
          >
            github
          </a>
        </div>
        <nav className="feed-tabs" aria-label="Event filters">
          {tabs.map((tab) => (
            <button
              key={tab.value}
              onClick={() => onFilterChange(tab.value)}
              className={activeFilter === tab.value ? "feed-tab is-active" : "feed-tab"}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
}
