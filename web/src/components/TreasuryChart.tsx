import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { getTreasurySnapshots, type TreasurySnapshotsData } from "@/lib/gnars-data";

export function TreasuryChart() {
  const [data, setData] = useState<TreasurySnapshotsData | null>(null);

  useEffect(() => {
    getTreasurySnapshots().then(setData);
  }, []);

  if (!data || !data.records.length) {
    return <div className="analytics-note">Carregando Treasury Data...</div>;
  }

  const chartData = data.records.map(r => ({
    date: r.date,
    value: r.total_value_usd
  }));

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
        <h3 className="analytics-block-title">Treasury × Tempo</h3>
      </div>

      <div style={{ width: "100%", height: 300, marginTop: 16 }}>
        <ResponsiveContainer>
          <LineChart data={chartData} margin={{ top: 10, right: 10, bottom: 10, left: -20 }}>
            <XAxis
              dataKey="date"
              tickFormatter={dtFormatter}
              tick={{ fill: "#878580", fontSize: 11, fontFamily: "IBM Plex Mono" }}
              axisLine={{ stroke: "#403e3c" }}
              tickLine={false}
            />
            <YAxis
              tickFormatter={formatter}
              tick={{ fill: "#878580", fontSize: 11, fontFamily: "IBM Plex Mono" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              labelFormatter={dtFormatter}
              formatter={(val: number) => [formatter(val), "Treasury"]}
              contentStyle={{
                backgroundColor: "#282726",
                border: "1px solid #403e3c",
                borderRadius: 4,
                fontFamily: "IBM Plex Mono",
                fontSize: 12,
                color: "#cecdc3",
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="hsl(145, 60%, 50%)"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
