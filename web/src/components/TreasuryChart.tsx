import { useEffect, useState } from "react";
import {
  Area,
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
  treasuryEvents?: Array<{
    proposal_id: string;
    title: string;
    amount_usd: number;
    asset: string;
    amount: number;
    executed_at: string;
    balance_after: number;
  }>;
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

function HistoryRow({ row }: { row: NonNullable<TreasuryChartProps["treasuryEvents"]>[number] }) {
  const parts = row.proposal_id.split("-");
  const proposalNumber = parts[parts.length - 1];
  const shortTitle = row.title.length > 38 ? `${row.title.slice(0, 37)}...` : row.title;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr auto auto",
        gap: 10,
        fontSize: 9,
        fontFamily: "'Courier New', monospace",
        lineHeight: 1.45,
        padding: "2px 0",
      }}
    >
      <span style={{ color: "var(--b600)" }}>{`[#${proposalNumber}] ${shortTitle}`}</span>
      <span style={{ color: "var(--reL)" }}>{`-$${Math.round(row.amount_usd).toLocaleString()}`}</span>
      <span style={{ color: "var(--b500)" }}>{`→ $${Math.round(row.balance_after).toLocaleString()}`}</span>
    </div>
  );
}

export function TreasuryChart({
  projectedZeroDate,
  funding,
  proposalTags = [],
  currentTreasuryUsd,
  treasuryEvents = [],
}: TreasuryChartProps) {
  const [data, setData] = useState<TreasurySnapshotsData | null>(null);
  const [showHistory, setShowHistory] = useState(false);

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
  const yMax = mergedData.reduce((max, row) => {
    const rowMax = Math.max(row.value || 0, row.proposalSpend || 0, row.auctionInflow || 0);
    return Math.max(max, rowMax);
  }, 0);
  const yDomainMax = yMax > 0 ? Math.ceil(yMax * 1.1) : 350000;
  const projectedDateTick = mergedData.find((row) => row.date.startsWith(projectedZeroDate || ""))?.date;
  const currentValue = chartData[chartData.length - 1]?.value || 0;
  const peakValue = chartData.reduce((max, row) => Math.max(max, row.value), 0);

  const formatter = (value: number) => {
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}m`;
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}k`;
    return `$${value}`;
  };

  const historyRows = treasuryEvents.slice(0, 8);
  const historyCollapsed = historyRows.length > 5 && !showHistory;

  return (
    <div>
      <div className="treasury-chart-header">
        <div>
          <div className="treasury-total-value">{formatter(currentValue)}</div>
          <div className="analytics-note">Live treasury balance</div>
          {historyRows.length ? (
            <div style={{ marginTop: 8 }}>
              {historyRows.length > 5 ? (
                <button
                  type="button"
                  className="skt"
                  onClick={() => setShowHistory((value) => !value)}
                  style={{ marginBottom: 4 }}
                >
                  {historyCollapsed ? "show history" : "hide history"}
                </button>
              ) : null}
              <div>
                {(historyCollapsed ? historyRows.slice(0, 5) : historyRows).map((row) => (
                  <HistoryRow key={`${row.proposal_id}:${row.executed_at}:${row.amount_usd}`} row={row} />
                ))}
              </div>
            </div>
          ) : null}
        </div>
        <div className="treasury-total-value" style={{ marginLeft: "auto" }}>Peak {formatter(peakValue)}</div>
      </div>

      <div style={{ width: "100%", height: 300, marginTop: 16 }}>
        <ResponsiveContainer>
          <ComposedChart data={mergedData} margin={{ top: 10, right: 10, bottom: 10, left: -20 }}>
            <CartesianGrid strokeDasharray="4 4" stroke="var(--b150)" />
            <XAxis
              dataKey="date"
              tickFormatter={fmtDate}
              tick={{ fill: "var(--b500)", fontSize: 8, fontFamily: "'Courier New'" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[0, yDomainMax]}
              tickFormatter={fmtUSD}
              width={52}
              tick={{ fill: "var(--b500)", fontSize: 9, fontFamily: "'Courier New'" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              content={({ active, label, payload }) => {
                if (!active || !payload || !payload.length) return null;
                return (
                  <div
                    style={{
                      background: "#282726",
                      color: "#FFFEF8",
                      fontSize: 10,
                      fontFamily: "'Courier New', monospace",
                      padding: "8px 12px",
                      borderRadius: 2,
                      border: "none",
                    }}
                  >
                    <div style={{ marginBottom: 6 }}>{fmtDate(String(label || ""))}</div>
                    {payload.map((entry) => (
                      <div key={String(entry.name)} style={{ display: "flex", gap: 8, justifyContent: "space-between" }}>
                        <span>{String(entry.name)}</span>
                        <span>{fmtUSD(Number(entry.value || 0))}</span>
                      </div>
                    ))}
                  </div>
                );
              }}
            />
            <ReferenceLine
              y={10000}
              stroke="#DA702C"
              strokeDasharray="4 3"
              opacity={0.4}
              label={{ value: "$10k critical", fontSize: 8, fill: "#DA702C", fontFamily: "'Courier New'" }}
            />
            {projectedDateTick ? (
              <ReferenceLine x={projectedDateTick} stroke="#D14D41" strokeDasharray="5 4" label={{ value: "Projected zero", angle: -90, position: "insideTop", fill: "#D14D41", fontSize: 10 }} />
            ) : null}

            <Area
              type="monotone"
              dataKey="value"
              name="Balance fill"
              fill="rgba(64,62,60,0.05)"
              stroke="none"
            />

            <Bar
              dataKey="proposalSpend"
              name="Proposal spend"
              fill="rgba(209,77,65,0.18)"
              stroke="#D14D41"
              strokeWidth={1}
              barSize={14}
            />

            <Line
              type="monotone"
              dataKey="auctionInflow"
              name="Auction inflow"
              stroke="#879A39"
              strokeDasharray="5 3"
              strokeWidth={1.5}
              dot={false}
            />

            <Line
              type="monotone"
              dataKey="value"
              name="Balance"
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
