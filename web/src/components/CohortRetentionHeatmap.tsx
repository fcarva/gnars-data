import type { GrowthData } from "@/lib/gnars-data";

interface CohortRetentionHeatmapProps {
  data: GrowthData | null;
}

const OFFSETS: Array<{ key: "m_plus_1" | "m_plus_3" | "m_plus_6" | "m_plus_12"; label: string }> = [
  { key: "m_plus_1", label: "M+1" },
  { key: "m_plus_3", label: "M+3" },
  { key: "m_plus_6", label: "M+6" },
  { key: "m_plus_12", label: "M+12" },
];

function pctColor(value: number | null): string {
  if (value === null || value === undefined) return "rgba(64, 62, 60, 0.2)";
  const ratio = Math.max(0, Math.min(1, value / 100));
  const alpha = 0.2 + ratio * 0.7;
  return `rgba(102, 128, 11, ${alpha.toFixed(3)})`;
}

export function CohortRetentionHeatmap({ data }: CohortRetentionHeatmapProps) {
  const rows = (data?.cohort_retention || []).slice(-12);
  if (!rows.length) {
    return <div className="analytics-note">No cohort retention data available.</div>;
  }

  return (
    <div>
      <div className="analytics-block-title">VOTER COHORT RETENTION</div>
      <div className="analytics-cohort-wrap">
        <div className="analytics-cohort-head">
          <span>Cohort</span>
          {OFFSETS.map((offset) => (
            <span key={offset.key}>{offset.label}</span>
          ))}
        </div>
        <div className="analytics-cohort-body">
          {rows.map((row) => (
            <div key={row.cohort_month} className="analytics-cohort-row">
              <span className="analytics-cohort-label" title={`size ${row.cohort_size}`}>
                {row.cohort_month}
              </span>
              {OFFSETS.map((offset) => {
                const value = row[offset.key];
                return (
                  <span
                    key={`${row.cohort_month}-${offset.key}`}
                    className="analytics-cohort-cell"
                    style={{ background: pctColor(value) }}
                    title={value == null ? `${offset.label}: n/a` : `${offset.label}: ${value.toFixed(1)}%`}
                  >
                    {value == null ? "-" : `${value.toFixed(0)}%`}
                  </span>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
