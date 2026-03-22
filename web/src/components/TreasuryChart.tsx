import { useEffect, useState } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getTreasurySnapshots, type TreasurySnapshotsData, type FundingAnalysis, type ProposalTagRecord } from "@/lib/gnars-data";

interface TreasuryChartProps {
  projectedZeroDate?: string | null;
  funding?: FundingAnalysis | null;
  proposalTags?: ProposalTagRecord[];
  currentTreasuryUsd?: number | null;
  monthlyBurnUsd?: number | null;
  runwayMonths?: number | null;
  chartHeight?: number;
}

function fmtUSD(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}m`;
  if (value >= 1_000) return `$${Math.round(value / 1_000)}k`;
  return `$${Math.round(value).toLocaleString()}`;
}

function fmtDate(dateStr: string): string {
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" }).replace(" ", " '");
}

function monthLabel(iso: string): string {
  if (!iso) return "";
  const [year, month] = iso.split("-");
  const names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const idx = Number.parseInt(month || "0", 10) - 1;
  if (idx < 0 || idx > 11 || !year) return iso;
  return `${names[idx]} '${year.slice(2)}`;
}

function fmtAxisUSD(value: number): string {
  const v = Number(value) || 0;
  return v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}`;
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ dataKey?: string; value?: number }>; label?: string }) {
  if (!active || !payload?.length) return null;
  const balance = payload.find((item) => item.dataKey === "balance")?.value;
  const spend = payload.find((item) => item.dataKey === "monthly_spend")?.value;
  const inflow = payload.find((item) => item.dataKey === "auction_inflow")?.value;
  return (
    <div
      style={{
        background: "#282726",
        color: "#FFFEF8",
        padding: "8px 12px",
        fontSize: 10,
        fontFamily: "'Courier New', monospace",
        lineHeight: 1.8,
        borderRadius: 2,
        border: "none",
        boxShadow: "none",
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{monthLabel(String(label || ""))}</div>
      {balance != null ? <div>{`Balance: ${fmtUSD(Number(balance))}`}</div> : null}
      {spend != null && Number(spend) > 0 ? <div style={{ color: "#F09595" }}>{`Spend: ${fmtUSD(Number(spend))}`}</div> : null}
      {inflow != null && Number(inflow) > 0 ? <div style={{ color: "#B7D36B" }}>{`Auction inflow: ${fmtUSD(Number(inflow))}`}</div> : null}
    </div>
  );
}

export function TreasuryChart({
  projectedZeroDate,
  funding,
  proposalTags = [],
  currentTreasuryUsd,
  monthlyBurnUsd,
  runwayMonths,
  chartHeight = 200,
}: TreasuryChartProps) {
  const [data, setData] = useState<TreasurySnapshotsData | null>(null);

  useEffect(() => {
    getTreasurySnapshots()
      .then(setData)
      .catch(() => setData(null));
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
      return { date: `${month}-01`, value: Math.max(balance, 0), proposalSpend: spendByMonth.get(month) || 0 };
    });
    if (currentTreasuryUsd && synthetic.length) {
      const last = synthetic[synthetic.length - 1];
      const nowMonth = new Date().toISOString().slice(0, 7);
      if (!last.date.startsWith(nowMonth)) {
        synthetic.push({ date: `${nowMonth}-01`, value: currentTreasuryUsd, proposalSpend: 0 });
      } else {
        last.value = currentTreasuryUsd;
      }
    }
    return synthetic;
  })();

  const tagByArchive = new Map(proposalTags.map((row) => [row.archive_id, row.semantic_category || row.primary_category || "other"]));

  const spendByMonthCategory = new Map<string, number>();

  for (const row of funding?.allocation_by_proposal || []) {
    const month = (row.created_at || "").slice(0, 7);
    if (!month) continue;
    if (!spendByMonthCategory.has(month)) {
      spendByMonthCategory.set(month, 0);
    }
    const amount = row.executed_spend_usd || 0;
    const category = tagByArchive.get(row.archive_id) || "other";
    if (
      category === "athletes_riders"
      || category === "workstream_media"
      || category === "workstream_ops"
      || category === "workstream_products"
      || category === "workstream_dev"
      || category === "irl_events"
      || category === "other"
    ) {
      spendByMonthCategory.set(month, (spendByMonthCategory.get(month) || 0) + amount);
    }
  }

  const auctionByMonth = new Map<string, number>();
  for (const source of funding?.funding_sources || []) {
    const marker = `${source.funding_source_id} ${source.title}`.toLowerCase();
    if (!marker.includes("auction")) continue;
    const month = (source.source_date || "").slice(0, 7);
    if (!month) continue;
    auctionByMonth.set(month, (auctionByMonth.get(month) || 0) + (source.usd_estimate_at_source || 0));
  }

  if (auctionByMonth.size === 0 && (funding?.summary.auction_revenue_usd_estimate || 0) > 0 && chartData.length) {
    const latestMonth = chartData[chartData.length - 1].date.slice(0, 7);
    auctionByMonth.set(latestMonth, funding?.summary.auction_revenue_usd_estimate || 0);
  }

  const mergedByMonth = new Map<
    string,
    { date: string; value: number; proposalSpend: number; auctionInflow: number }
  >();
  for (const row of chartData) {
    const month = row.date.slice(0, 7);
    mergedByMonth.set(month, {
      date: `${month}-01`,
      value: row.value,
      proposalSpend: 0,
      auctionInflow: 0,
    });
  }
  for (const [month, spend] of spendByMonthCategory.entries()) {
    const existing = mergedByMonth.get(month);
    if (existing) {
      existing.proposalSpend = spend;
    } else {
      mergedByMonth.set(month, {
        date: `${month}-01`,
        value: 0,
        proposalSpend: spend,
        auctionInflow: 0,
      });
    }
  }

  for (const [month, inflow] of auctionByMonth.entries()) {
    const existing = mergedByMonth.get(month);
    if (existing) {
      existing.auctionInflow = inflow;
    } else {
      mergedByMonth.set(month, {
        date: `${month}-01`,
        value: 0,
        proposalSpend: 0,
        auctionInflow: inflow,
      });
    }
  }

  const mergedData = Array.from(mergedByMonth.values()).sort((a, b) => a.date.localeCompare(b.date));
  const chartRows =
    (data.history || []).length > 0
      ? (data.history || []).map((row) => ({
          month: row.month,
          balance: row.balance,
          monthly_spend: row.monthly_spend,
          auction_inflow: row.auction_inflow,
        }))
      : mergedData.map((row) => ({
          month: row.date.slice(0, 7),
          balance: row.value,
          monthly_spend: row.proposalSpend,
          auction_inflow: row.auctionInflow,
        }));
  const projectedDateTick = chartRows.find((row) => row.month.startsWith(projectedZeroDate || ""))?.month;
  const currentValue = chartData[chartData.length - 1]?.value || 0;
  const peakValue = chartData.reduce((max, row) => Math.max(max, row.value), 0);
  const burn = typeof monthlyBurnUsd === "number" ? monthlyBurnUsd : null;
  const runway = typeof runwayMonths === "number" ? runwayMonths : null;

  return (
    <div>
      <div className="treasury-chart-header">
        <div className="treasury-total-value">{`$${Math.round(currentValue).toLocaleString("en-US")}`}</div>
        <div className="treasury-metrics-inline">
          <span>{`Peak $${Math.round(peakValue).toLocaleString("en-US")}`}</span>
          <span>{`Burn/Mo ${burn != null ? `$${Math.round(burn).toLocaleString("en-US")}` : "-"}`}</span>
          <span>{`Runway ${runway != null ? `${Math.round(runway)} mo` : "-"}`}</span>
        </div>
      </div>

      <div style={{ width: "100%", height: chartHeight, marginTop: 10 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartRows} margin={{ top: 8, right: 44, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 0" vertical={false} stroke="#E6E4D9" strokeWidth={0.5} />
            <XAxis
              dataKey="month"
              tickFormatter={(value: string) => monthLabel(value)}
              tick={{ fill: "#6F6E69", fontSize: 9, fontFamily: "'Courier New', monospace" }}
              axisLine={false}
              tickLine={false}
              interval="preserveStartEnd"
              minTickGap={60}
            />
            <YAxis
              yAxisId="balance"
              orientation="left"
              domain={[0, "auto"]}
              tickFormatter={fmtAxisUSD}
              tick={{ fontSize: 9, fontFamily: "'Courier New', monospace", fill: "#6F6E69" }}
              axisLine={false}
              tickLine={false}
              width={48}
              tickCount={5}
            />
            <YAxis
              yAxisId="spend"
              orientation="right"
              domain={[0, "auto"]}
              tickFormatter={fmtAxisUSD}
              tick={{ fontSize: 8, fontFamily: "'Courier New', monospace", fill: "#B7B5AC" }}
              axisLine={false}
              tickLine={false}
              width={36}
              tickCount={4}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              yAxisId="balance"
              y={10000}
              stroke="#DA702C"
              strokeDasharray="4 3"
              strokeOpacity={0.5}
            />
            {projectedDateTick ? (
              <ReferenceLine x={projectedDateTick} stroke="#D14D41" strokeDasharray="5 4" />
            ) : null}

            <Bar
              yAxisId="spend"
              dataKey="monthly_spend"
              name="Spend"
              fill="rgba(209,77,65,0.20)"
              stroke="#D14D41"
              strokeWidth={1}
              radius={[2, 2, 0, 0]}
              maxBarSize={10}
            />

            <Line
              yAxisId="spend"
              type="monotone"
              dataKey="auction_inflow"
              name="Auction inflow"
              stroke="#879A39"
              strokeDasharray="5 3"
              strokeWidth={1.5}
              dot={{ r: 2.5, fill: "#879A39", strokeWidth: 0 }}
              connectNulls={false}
            />

            <Line
              yAxisId="balance"
              type="monotone"
              dataKey="balance"
              name="Balance"
              stroke="#403E3C"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 3, fill: "#403E3C" }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div style={{ display: "flex", gap: 14, marginTop: 10, flexWrap: "wrap" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 8.5, color: "#6F6E69" }}>
          <span style={{ display: "inline-block", width: 14, height: 2, background: "#403E3C" }} />
          Balance
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 8.5, color: "#6F6E69" }}>
          <span style={{ display: "inline-block", width: 10, height: 10, background: "rgba(209,77,65,0.22)", border: "1px solid #D14D41", borderRadius: 1 }} />
          Monthly spend
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 8.5, color: "#6F6E69" }}>
          <span style={{ display: "inline-block", width: 14, height: 0, borderTop: "2px dashed #879A39" }} />
          Auction inflow
        </span>
      </div>
    </div>
  );
}
