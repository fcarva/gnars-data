import type { ActivityTimeseriesData } from "@/lib/gnars-data";

interface ActivityHeatmapProps {
  data: ActivityTimeseriesData | null;
}

interface CellPoint {
  date: string;
  weekIndex: number;
  dayIndex: number;
  value: number;
}

const DAY_MS = 24 * 60 * 60 * 1000;

function mondayIndex(date: Date): number {
  const d = date.getUTCDay();
  return d === 0 ? 6 : d - 1;
}

function toDateOnly(input: string): Date {
  return new Date(`${input}T00:00:00Z`);
}

function buildCells(data: ActivityTimeseriesData): { cells: CellPoint[]; max: number } {
  const byDate = new Map<string, number>();
  for (const row of data.records) {
    const score = (row.proposals_created || 0) + (row.proposals_closed || 0);
    byDate.set(row.date, score);
  }

  const latest = data.records.length ? toDateOnly(data.records[data.records.length - 1].date) : new Date();
  const start = new Date(latest.getTime() - 7 * 52 * DAY_MS + DAY_MS);

  const cells: CellPoint[] = [];
  let max = 0;

  for (let i = 0; i < 7 * 52; i += 1) {
    const current = new Date(start.getTime() + i * DAY_MS);
    const yyyy = current.getUTCFullYear();
    const mm = String(current.getUTCMonth() + 1).padStart(2, "0");
    const dd = String(current.getUTCDate()).padStart(2, "0");
    const key = `${yyyy}-${mm}-${dd}`;
    const value = byDate.get(key) || 0;
    if (value > max) max = value;

    cells.push({
      date: key,
      weekIndex: Math.floor(i / 7),
      dayIndex: mondayIndex(current),
      value,
    });
  }

  return { cells, max };
}

function cellColor(value: number, max: number): string {
  if (value <= 0 || max <= 0) return "rgba(64, 62, 60, 0.2)";
  const ratio = value / max;
  const alpha = 0.2 + ratio * 0.7;
  return `rgba(32, 94, 166, ${alpha.toFixed(3)})`;
}

export function ActivityHeatmap({ data }: ActivityHeatmapProps) {
  if (!data || !data.records.length) {
    return <div className="analytics-note">No daily activity timeseries available.</div>;
  }

  const { cells, max } = buildCells(data);

  return (
    <div>
      <div className="analytics-block-title">PROPOSAL ACTIVITY HEATMAP (52W)</div>
      <div className="analytics-heatmap-wrap">
        <div className="analytics-heatmap-grid">
          {cells.map((cell) => (
            <div
              key={cell.date}
              className="analytics-heatmap-cell"
              style={{
                gridColumn: cell.weekIndex + 1,
                gridRow: cell.dayIndex + 1,
                background: cellColor(cell.value, max),
              }}
              title={`${cell.date} • activity ${cell.value}`}
            />
          ))}
        </div>
      </div>
      <div className="analytics-sankey-meta">
        <span>activity = proposals_created + proposals_closed</span>
        <span>peak day: {max}</span>
      </div>
    </div>
  );
}
