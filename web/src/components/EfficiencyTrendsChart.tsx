import { useMemo } from "react";
import { ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Bar } from "recharts";
import type { EfficiencyData, FundingAnalysis, ProposalTagRecord } from "@/lib/gnars-data";
import { fmtDate, fmtUSD } from "@/lib/format";

interface EfficiencyTrendsChartProps {
  data: EfficiencyData | null;
  funding: FundingAnalysis | null;
  proposalTags: ProposalTagRecord[];
}

export function EfficiencyTrendsChart({ data, funding, proposalTags }: EfficiencyTrendsChartProps) {
  const points = data?.timeseries || [];
  if (!points.length) {
    return <div className="analytics-note">No efficiency timeseries available.</div>;
  }

  const tagByArchive = useMemo(() => {
    return new Map(proposalTags.map((row) => [row.archive_id, row.semantic_category || row.primary_category || "other"]));
  }, [proposalTags]);

  const categoryKeys = ["athletes", "media", "operations", "devEvents", "other"] as const;
  type CategoryKey = (typeof categoryKeys)[number];
  type MonthRow = { month: string } & Record<CategoryKey, number>;
  const categoryMeta: Record<(typeof categoryKeys)[number], { label: string; color: string }> = {
    athletes: { label: "Athletes", color: "#3AA99F" },
    media: { label: "Media", color: "#8B7EC8" },
    operations: { label: "Operations", color: "#DA702C" },
    devEvents: { label: "Dev + Events", color: "#4385BE" },
    other: { label: "Other", color: "#B7B5AC" },
  };

  const monthBuckets = useMemo(() => {
    const rows = new Map<string, MonthRow>();
    for (const row of funding?.allocation_by_proposal || []) {
      const month = (row.created_at || "").slice(0, 7);
      if (!month) continue;
      const category = tagByArchive.get(row.archive_id) || "other";
      let key: CategoryKey = "other";
      if (category === "athletes_riders") key = "athletes";
      else if (category === "workstream_media") key = "media";
      else if (category === "workstream_ops") key = "operations";
      else if (category === "workstream_products" || category === "workstream_dev" || category === "irl_events") key = "devEvents";
      const current: MonthRow = rows.get(month) || {
        month,
        athletes: 0,
        media: 0,
        operations: 0,
        devEvents: 0,
        other: 0,
      };
      current[key] += row.executed_spend_usd || 0;
      rows.set(month, current);
    }
    return Array.from(rows.values()).sort((a, b) => a.month.localeCompare(b.month));
  }, [funding?.allocation_by_proposal, tagByArchive]);

  if (!monthBuckets.length) {
    return <div className="analytics-note">No monthly category spend data available.</div>;
  }

  return (
    <div>
      <div className="analytics-note" style={{ marginBottom: 10 }}>
        Monthly stacked spend by proposal category.
      </div>
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <BarChart data={monthBuckets} margin={{ top: 10, right: 12, bottom: 10, left: -12 }}>
            <CartesianGrid strokeDasharray="4 4" stroke="#E6E4D9" vertical={false} />
            <XAxis
              dataKey="month"
              tickFormatter={(value) => fmtDate(String(value))}
              tick={{ fill: "#878580", fontSize: 11, fontFamily: "IBM Plex Mono" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tickFormatter={(value) => fmtUSD(Number(value))}
              tick={{ fill: "#878580", fontSize: 11, fontFamily: "IBM Plex Mono" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              formatter={(value, name) => [fmtUSD(Number(value || 0)), String(name)]}
              labelFormatter={(label) => fmtDate(String(label))}
            />
            {categoryKeys.map((key) => (
              <Bar key={key} dataKey={key} stackId="spend" name={categoryMeta[key].label} fill={categoryMeta[key].color} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
