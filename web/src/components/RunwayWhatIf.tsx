import { useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DaoMetrics } from "@/lib/gnars-data";
import { fmtDate, fmtUSD } from "@/lib/format";

interface RunwayWhatIfProps {
  metrics: DaoMetrics;
}

function nextMonths(count: number): string[] {
  const out: string[] = [];
  const now = new Date();
  for (let i = 0; i < count; i += 1) {
    const d = new Date(now.getFullYear(), now.getMonth() + i, 1);
    out.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  }
  return out;
}

export function RunwayWhatIf({ metrics }: RunwayWhatIfProps) {
  const [simAsk, setSimAsk] = useState(5000);

  const balance = typeof metrics.treasury_balance_usd === "number"
    ? metrics.treasury_balance_usd
    : metrics.overview.treasury_total_value_usd;
  const burn = typeof metrics.monthly_burn_usd === "number" && metrics.monthly_burn_usd > 0
    ? metrics.monthly_burn_usd
    : 5300;

  const projection = useMemo(() => {
    const months = nextMonths(18);
    const rows = months.map((month, idx) => {
      const current = Math.max(0, balance - burn * idx);
      const low = Math.max(0, balance - 3000 * idx);
      const high = Math.max(0, balance - 8000 * idx);
      return {
        month,
        current,
        low,
        high,
      };
    });

    return rows;
  }, [balance, burn]);

  const runwayMonths = Math.max(0, Math.round(balance / burn));
  const zeroDate = metrics.projected_zero_date || (() => {
    const d = new Date();
    const zero = new Date(d.getFullYear(), d.getMonth() + runwayMonths, 1);
    return `${zero.getFullYear()}-${String(zero.getMonth() + 1).padStart(2, "0")}`;
  })();
  const simRunway = Math.max(0, Math.round((balance - simAsk) / burn));

  return (
    <div className="analytics-runway-wrap">
      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "8px" }}>
        <span style={{ background: "#F2F0E5", padding: "6px 12px", borderRadius: "6px", fontFamily: "var(--mono)", fontSize: "11px" }}>
          <strong>{runwayMonths} months</strong> at current burn
        </span>
        <span style={{ background: "#F2F0E5", padding: "6px 12px", borderRadius: "6px", fontFamily: "var(--mono)", fontSize: "11px" }}>
          <strong>{fmtDate(zeroDate)}</strong> projected zero
        </span>
        <span style={{ background: "#F2F0E5", padding: "6px 12px", borderRadius: "6px", fontFamily: "var(--mono)", fontSize: "11px" }}>
          <strong>{fmtUSD(burn)}</strong>/mo 30-day avg burn
        </span>
      </div>
      <div style={{ height: "140px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={projection} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" />
            <XAxis
              dataKey="month"
              tick={{ fill: "var(--muted)", fontSize: 10 }}
              tickLine={false}
              axisLine={{ stroke: "var(--line)" }}
              tickFormatter={fmtDate}
              minTickGap={28}
            />
            <YAxis
              tick={{ fill: "var(--muted)", fontSize: 11 }}
              tickFormatter={(value) => fmtUSD(Number(value))}
              axisLine={{ stroke: "var(--line)" }}
              tickLine={false}
              width={60}
              domain={[0, "auto"]}
            />
            <Tooltip
              formatter={(value) => [fmtUSD(Number(value ?? 0)), "Balance"]}
              labelFormatter={(label) => fmtDate(String(label))}
              contentStyle={{ background: "var(--surface)", border: "1px solid var(--line)", borderRadius: "8px" }}
            />
            <ReferenceLine
              y={10000}
              stroke="#D14D41"
              strokeOpacity={0.4}
              label={{ value: "critical $10k", fontSize: 9, fill: "#D14D41", position: "right" }}
            />
            <Line type="monotone" dataKey="current" stroke="#403E3C" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="low" stroke="#879A39" strokeWidth={2} strokeDasharray="5 3" dot={false} />
            <Line type="monotone" dataKey="high" stroke="#D14D41" strokeWidth={2} strokeDasharray="5 3" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", fontFamily: "var(--mono)", fontSize: "9px", color: "#6F6E69" }}>
        <span>if next proposal asks</span>
        <input type="range" min={1000} max={15000} step={500} value={simAsk} onChange={(e) => setSimAsk(Number(e.target.value))} />
        <strong style={{ color: "#282726", fontWeight: 700 }}>
          {fmtUSD(simAsk)} → runway drops to {simRunway} months
        </strong>
      </div>
    </div>
  );
}
