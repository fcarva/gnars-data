import { useEffect, useState } from "react";
import { ComposedChart, Line, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, CartesianGrid } from "recharts";
import { getTreasurySnapshots, type TreasurySnapshotsData, type FundingAnalysis, type ProposalTagRecord } from "@/lib/gnars-data";

interface TreasuryChartProps {
  projectedZeroDate?: string | null;
  funding?: FundingAnalysis | null;
  proposalTags?: ProposalTagRecord[];
  currentTreasuryUsd?: number | null;
}

export function TreasuryChart({ projectedZeroDate, funding, proposalTags = [], currentTreasuryUsd }: TreasuryChartProps) {
  const [data, setData] = useState<TreasurySnapshotsData | null>(null);

  useEffect(() => {
    getTreasurySnapshots().then(setData);
  }, []);

  if (!data || !data.records.length) {
    return <div className="analytics-note">Carregando Treasury Data...</div>;
  }

  const chartData = (() => {
    if (data.records.length > 1) {
      return data.records.map((r) => ({ date: r.date, value: r.total_value_usd }));
    }

    const start = funding?.summary.potential_funding_usd_estimate || funding?.summary.approved_funding_usd_estimate || null;
    const allocation = funding?.allocation_by_proposal || [];
    if (!start || allocation.length === 0) {
      return data.records.map((r) => ({ date: r.date, value: r.total_value_usd }));
    }

    const spendByMonth = new Map<string, number>();
    for (const row of allocation) {
      const month = (row.created_at || "").slice(0, 7);
      if (!month) continue;
      spendByMonth.set(month, (spendByMonth.get(month) || 0) + (row.executed_spend_usd || 0));
    }
    const months = Array.from(spendByMonth.keys()).sort((a, b) => a.localeCompare(b));
    let balance = start;
    const synthetic = months.map((month) => {
      balance -= spendByMonth.get(month) || 0;
      return { date: `${month}-01`, value: Math.max(balance, 0) };
    });
    if (currentTreasuryUsd && synthetic.length) {
      const last = synthetic[synthetic.length - 1];
      const nowMonth = new Date().toISOString().slice(0, 7);
      if (!last.date.startsWith(nowMonth)) {
        synthetic.push({ date: `${nowMonth}-01`, value: currentTreasuryUsd });
      } else {
        last.value = currentTreasuryUsd;
      }
    }
    return synthetic;
  })();

  const tagByArchive = new Map(proposalTags.map((row) => [row.archive_id, row.semantic_category || row.primary_category || "other"]));

  const spendByMonthCategory = new Map<
    string,
    { athletes: number; media: number; ops: number; devEvents: number; other: number }
  >();

  for (const row of funding?.allocation_by_proposal || []) {
    const month = (row.created_at || "").slice(0, 7);
    if (!month) continue;
    if (!spendByMonthCategory.has(month)) {
      spendByMonthCategory.set(month, { athletes: 0, media: 0, ops: 0, devEvents: 0, other: 0 });
    }
    const bucket = spendByMonthCategory.get(month);
    if (!bucket) continue;
    const amount = row.executed_spend_usd || 0;
    const category = tagByArchive.get(row.archive_id) || "other";
    if (category === "athletes_riders") bucket.athletes += amount;
    else if (category === "workstream_media") bucket.media += amount;
    else if (category === "workstream_ops") bucket.ops += amount;
    else if (category === "workstream_products" || category === "workstream_dev" || category === "irl_events") bucket.devEvents += amount;
    else bucket.other += amount;
  }

  const mergedByMonth = new Map<string, { date: string; value: number; athletes: number; media: number; ops: number; devEvents: number; other: number }>();
  for (const row of chartData) {
    const month = row.date.slice(0, 7);
    mergedByMonth.set(month, {
      date: `${month}-01`,
      value: row.value,
      athletes: 0,
      media: 0,
      ops: 0,
      devEvents: 0,
      other: 0,
    });
  }
  for (const [month, spend] of spendByMonthCategory.entries()) {
    const existing = mergedByMonth.get(month);
    if (existing) {
      existing.athletes = spend.athletes;
      existing.media = spend.media;
      existing.ops = spend.ops;
      existing.devEvents = spend.devEvents;
      existing.other = spend.other;
    } else {
      mergedByMonth.set(month, {
        date: `${month}-01`,
        value: 0,
        athletes: spend.athletes,
        media: spend.media,
        ops: spend.ops,
        devEvents: spend.devEvents,
        other: spend.other,
      });
    }
  }

  const mergedData = Array.from(mergedByMonth.values()).sort((a, b) => a.date.localeCompare(b.date));
  const projectedDateTick = mergedData.find((row) => row.date.startsWith(projectedZeroDate || ""))?.date;
  const currentValue = chartData[chartData.length - 1]?.value || 0;
  const peakValue = chartData.reduce((max, row) => Math.max(max, row.value), 0);

  const formatter = (value: number) => {
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}m`;
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}k`;
    return `$${value}`;
  };

  const dtFormatter = (dateStr: string) => {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" }).replace(" ", " '");
  };

  return (
    <div>
      <div className="treasury-chart-header">
        <div>
          <div className="treasury-total-value">{formatter(currentValue)}</div>
          <div className="analytics-note">Live treasury balance</div>
        </div>
        <div className="treasury-total-value" style={{ marginLeft: "auto" }}>Peak {formatter(peakValue)}</div>
      </div>

      <div style={{ width: "100%", height: 300, marginTop: 16 }}>
        <ResponsiveContainer>
          <ComposedChart data={mergedData} margin={{ top: 10, right: 10, bottom: 10, left: -20 }}>
            <CartesianGrid strokeDasharray="4 4" stroke="var(--b150)" />
            <XAxis
              dataKey="date"
              tickFormatter={dtFormatter}
              tick={{ fill: "var(--b500)", fontSize: 11, fontFamily: "IBM Plex Mono" }}
              axisLine={{ stroke: "var(--b150)" }}
              tickLine={false}
            />
            <YAxis
              tickFormatter={formatter}
              tick={{ fill: "var(--b500)", fontSize: 11, fontFamily: "IBM Plex Mono" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              labelFormatter={(label) => dtFormatter(String(label || ""))}
              formatter={(val, name) => {
                if (name === "Treasury") return [formatter(Number(val || 0)), "Treasury"];
                return [formatter(Number(val || 0)), name];
              }}
              contentStyle={{
                backgroundColor: "var(--pp)",
                border: "1px solid var(--b150)",
                borderRadius: 4,
                fontFamily: "IBM Plex Mono",
                fontSize: 12,
                color: "var(--b900)",
              }}
            />
            <ReferenceLine y={10000} stroke="#DA702C" strokeDasharray="4 4" label={{ value: "$10k", position: "insideTopRight", fill: "#DA702C", fontSize: 11 }} />
            {projectedDateTick ? (
              <ReferenceLine x={projectedDateTick} stroke="#D14D41" strokeDasharray="5 4" label={{ value: "Projected zero", angle: -90, position: "insideTop", fill: "#D14D41", fontSize: 10 }} />
            ) : null}

            <Bar dataKey="athletes" stackId="spend" fill="#3AA99F" name="Athletes spend" barSize={14} />
            <Bar dataKey="media" stackId="spend" fill="#8B7EC8" name="Media spend" barSize={14} />
            <Bar dataKey="ops" stackId="spend" fill="#DA702C" name="Ops spend" barSize={14} />
            <Bar dataKey="devEvents" stackId="spend" fill="#4385BE" name="Dev + Events spend" barSize={14} />
            <Bar dataKey="other" stackId="spend" fill="#B7B5AC" name="Other spend" barSize={14} />

            <Line
              type="monotone"
              dataKey="value"
              name="Treasury"
              stroke="#403E3C"
              strokeWidth={2}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="analytics-note" style={{ marginTop: 10 }}>
        Monthly stacked spend by proposal category over treasury balance.
      </div>
    </div>
  );
}
