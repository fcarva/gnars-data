import { useState } from "react";

interface TreasuryEvent {
  proposal_id: string;
  title: string;
  amount_usd: number;
  executed_at: string;
  balance_after: number;
}

interface TreasuryLedgerProps {
  events: TreasuryEvent[];
}

function LedgerRow({ row }: { row: TreasuryEvent }) {
  const parts = row.proposal_id.split("-");
  const proposalNumber = parts[parts.length - 1];
  const amountText = `−$${Math.round(row.amount_usd).toLocaleString("en-US")}`;
  const balanceText = `$${Math.round(row.balance_after).toLocaleString("en-US")}`;

  return (
    <div className="treasury-ledger-row">
      <span className="treasury-ledger-badge">#{proposalNumber}</span>
      <span className="treasury-ledger-title" title={row.title}>{row.title}</span>
      <span className="treasury-ledger-amount">{amountText}</span>
      <span className="treasury-ledger-balance">{balanceText}</span>
    </div>
  );
}

export function TreasuryLedger({ events }: TreasuryLedgerProps) {
  const [showAll, setShowAll] = useState(false);
  const rows = events.slice(0, 12);
  const visibleRows = showAll ? rows : rows.slice(0, 3);
  const hasOverflowRows = rows.length > 3;

  if (!rows.length) {
    return null;
  }

  return (
    <section className="treasury-ledger-block">
      <div className="treasury-ledger-head">
        <span>RECENT OUTFLOWS</span>
        {hasOverflowRows ? (
          <button
            type="button"
            className="treasury-ledger-toggle"
            onClick={() => setShowAll((value) => !value)}
          >
            {showAll ? "show less ↑" : "show all ↓"}
          </button>
        ) : null}
      </div>
      <div className="treasury-ledger-list">
        {visibleRows.map((row) => (
          <LedgerRow key={`${row.proposal_id}:${row.executed_at}:${row.amount_usd}`} row={row} />
        ))}
      </div>
    </section>
  );
}
