import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { DaoMetrics } from "@/lib/gnars-data";

const assetColors: Record<string, string> = {
  USDC: "hsl(200, 70%, 55%)",
  SENDIT: "hsl(30, 85%, 55%)",
  WETH: "hsl(280, 50%, 60%)",
  GNARS: "hsl(145, 60%, 50%)",
  SKATEHACKER: "hsl(330, 55%, 55%)",
  ZIMARDRP: "hsl(50, 80%, 55%)",
};

interface TreasuryChartProps {
  metrics: DaoMetrics;
}

export function TreasuryChart({ metrics }: TreasuryChartProps) {
  const assets = metrics.treasury.assets
    .filter((a) => a.value_usd > 0.5)
    .sort((a, b) => b.value_usd - a.value_usd);

  const totalUsd = metrics.treasury.treasury_page_total_value_usd || 1;

  return (
    <div>
      <div className="treasury-chart-header">
        <h3 className="analytics-block-title">TREASURY</h3>
        <span className="treasury-total-value">
          ${totalUsd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        </span>
      </div>

      <div className="treasury-composition-bar">
        {assets.map((asset) => {
          const pct = (asset.value_usd / totalUsd) * 100;
          return (
            <div
              key={asset.symbol}
              style={{
                width: `${pct}%`,
                backgroundColor: assetColors[asset.symbol] || "hsl(0, 0%, 30%)",
              }}
              title={`${asset.symbol}: $${asset.value_usd.toFixed(2)}`}
            />
          );
        })}
      </div>

      <div className="treasury-legend">
        {assets.map((asset) => (
          <div key={asset.symbol} className="treasury-legend-item">
            <div
              className="treasury-legend-dot"
              style={{ backgroundColor: assetColors[asset.symbol] || "hsl(0, 0%, 30%)" }}
            />
            <span className="treasury-legend-symbol">{asset.symbol}</span>
            <span className="treasury-legend-value">
              ${asset.value_usd >= 1000 ? `${(asset.value_usd / 1000).toFixed(1)}k` : asset.value_usd.toFixed(2)}
            </span>
          </div>
        ))}
      </div>

      <div className="treasury-chart-body">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={assets} layout="vertical" margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="symbol"
              width={70}
              tick={{ fill: "#878580", fontSize: 11, fontFamily: "IBM Plex Mono" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              formatter={(value) => {
                const n = typeof value === "number" ? value : Number(value ?? 0);
                return [`$${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}`, "Value"];
              }}
              contentStyle={{
                backgroundColor: "#282726",
                border: "1px solid #403e3c",
                borderRadius: 4,
                fontFamily: "IBM Plex Mono",
                fontSize: 12,
                color: "#cecdc3",
              }}
              cursor={{ fill: "#1c1b1a" }}
            />
            <Bar dataKey="value_usd" radius={[0, 2, 2, 0]}>
              {assets.map((asset) => (
                <Cell key={asset.symbol} fill={assetColors[asset.symbol] || "hsl(0, 0%, 30%)"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="treasury-outflows">
        <div>
          <span className="treasury-outflows-label">OUTFLOWS ETH</span>
          <span className="treasury-outflows-value">{metrics.overview.outflows_eth.toFixed(2)}</span>
        </div>
        <div>
          <span className="treasury-outflows-label">OUTFLOWS USDC</span>
          <span className="treasury-outflows-value">${metrics.overview.outflows_usdc.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
