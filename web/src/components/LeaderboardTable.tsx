import type { LeaderboardEntry } from "@/lib/gnars-data";

interface LeaderboardTableProps {
  title: string;
  entries: LeaderboardEntry[];
  formatValue?: (value: number) => string;
}

export function LeaderboardTable({ title, entries, formatValue }: LeaderboardTableProps) {
  return (
    <div className="analytics-table-wrap">
      <h4 className="analytics-block-title">{title}</h4>
      <div className="analytics-table">
        {entries.slice(0, 8).map((entry, index) => (
          <div key={`${entry.address}-${index}`} className="analytics-table-row">
            <span className="analytics-table-rank">{index + 1}</span>
            <span className="analytics-table-name">{entry.display_name || entry.slug || entry.address}</span>
            <span className="analytics-table-value">{formatValue ? formatValue(entry.value) : entry.value.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
