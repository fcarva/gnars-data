import { formatAmount, formatAssetSymbol } from "../lib/format";
import type { AssetAmount } from "../types";

export function AssetBars({
  items,
  emptyLabel = "No recorded flows",
}: {
  items: AssetAmount[];
  emptyLabel?: string;
}) {
  const maxValue = Math.max(1, ...items.map((item) => item.amount));

  if (!items.length) {
    return <article className="mini-row static"><span>Assets</span><strong>{emptyLabel}</strong></article>;
  }

  return (
    <div className="bar-stack">
      {items.map((item) => (
        <div key={`${item.symbol}:${item.amount}`} className="bar-row">
          <div className="bar-meta">
            <span>{formatAssetSymbol(item.symbol)}</span>
            <strong>{formatAmount(item.symbol, item.amount)}</strong>
          </div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${Math.max(6, (item.amount / maxValue) * 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}
