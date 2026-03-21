import { useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { RunwayScenariosData } from "@/lib/gnars-data";

interface RunwayWhatIfProps {
  data: RunwayScenariosData | null;
}

function fmtUsd(value: number): string {
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export function RunwayWhatIf({ data }: RunwayWhatIfProps) {
  const [burnMultiplier, setBurnMultiplier] = useState(100);
  const [monthlyInflow, setMonthlyInflow] = useState(0);

  const projection = useMemo(() => {
    if (!data) return null;

    const baseline = data.overview.baseline_monthly_burn_usd;
    const burn = baseline * (burnMultiplier / 100);
    let balance = data.overview.treasury_balance_usd;
    let runway = 0;

    const rows = Array.from({ length: 25 }).map((_, idx) => {
      const month = idx === 0
        ? data.scenarios[0]?.projection[0]?.month || "now"
        : data.scenarios[0]?.projection[idx]?.month || `M+${idx}`;
      if (idx > 0) {
        balance = Math.max(0, balance + monthlyInflow - burn);
      }
      if (balance > 0) {
        runway = idx;
      }
      return {
        month,
        balance_usd: Math.round(balance),
      };
    });

    return {
      runway,
      burn,
      rows,
    };
  }, [burnMultiplier, data, monthlyInflow]);

  if (!data || !projection) {
    return <div className="analytics-note">No runway scenarios available.</div>;
  }

  return (
    <div className="analytics-runway-wrap">
      <div className="analytics-runway-controls">
        <label className="analytics-runway-control">
          <span>Burn Multiplier: {burnMultiplier}%</span>
          <input
            type="range"
            min={50}
            max={200}
            step={5}
            value={burnMultiplier}
            onChange={(event) => setBurnMultiplier(Number(event.target.value))}
          />
        </label>
        <label className="analytics-runway-control">
          <span>Monthly Inflow: {fmtUsd(monthlyInflow)}</span>
          <input
            type="range"
            min={0}
            max={4000}
            step={100}
            value={monthlyInflow}
            onChange={(event) => setMonthlyInflow(Number(event.target.value))}
          />
        </label>
      </div>

      <div className="analytics-overview-grid analytics-overview-grid-compact">
        <div className="analytics-overview-card">
          <div className="analytics-overview-label">CURRENT BALANCE</div>
          <div className="analytics-overview-value">{fmtUsd(data.overview.treasury_balance_usd)}</div>
        </div>
        <div className="analytics-overview-card">
          <div className="analytics-overview-label">MONTHLY BURN</div>
          <div className="analytics-overview-value">{fmtUsd(projection.burn)}</div>
        </div>
        <div className="analytics-overview-card">
          <div className="analytics-overview-label">RUNWAY</div>
          <div className="analytics-overview-value">{projection.runway} months</div>
        </div>
      </div>

      <div className="analytics-timeseries-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={projection.rows} margin={{ top: 8, right: 20, left: 10, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" />
            <XAxis dataKey="month" tick={{ fill: "var(--muted)", fontSize: 10 }} tickLine={false} axisLine={{ stroke: "var(--line)" }} minTickGap={28} />
            <YAxis tick={{ fill: "var(--muted)", fontSize: 11 }} tickFormatter={(value) => `$${Math.round(value / 1000)}k`} axisLine={{ stroke: "var(--line)" }} tickLine={false} width={52} />
            <Tooltip
              formatter={(value) => [fmtUsd(Number(value ?? 0)), "Balance"]}
              labelFormatter={(label) => `Month ${label}`}
              contentStyle={{ background: "var(--surface)", border: "1px solid var(--line)", borderRadius: "8px" }}
            />
            <Line type="monotone" dataKey="balance_usd" stroke="var(--accent)" strokeWidth={2.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
