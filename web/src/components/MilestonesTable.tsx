import type { MilestoneRecord } from "@/lib/gnars-data";

interface MilestonesTableProps {
  records: MilestoneRecord[];
  title: string;
  emptyMessage: string;
}

function displayStatus(status: string): string {
  const value = status.toLowerCase();
  if (value === "completed") return "COMPLETED";
  if (value === "in-progress") return "IN PROGRESS";
  if (value === "active") return "ACTIVE";
  if (value === "planned") return "PLANNED";
  return value ? value.toUpperCase() : "UNKNOWN";
}

function badgeClass(status: string): string {
  const value = status.toLowerCase();
  if (value === "completed") return "milestone-badge is-completed";
  if (value === "in-progress" || value === "active") return "milestone-badge is-in-progress";
  return "milestone-badge is-planned";
}

export function MilestonesTable({ records, title, emptyMessage }: MilestonesTableProps) {
  return (
    <section className="section-block">
      <div className="section-head compact-head">
        <span className="eyebrow">Delivery Stream</span>
        <h2>{title}</h2>
      </div>

      <div className="ledger-table compact-ledger">
        <div className="ledger-head">
          <span>Milestone</span>
          <span>Project</span>
          <span>Status</span>
          <span>Date</span>
        </div>
        <div className="ledger-body">
          {records.length === 0 ? (
            <div className="ledger-empty">
              <strong>{emptyMessage}</strong>
            </div>
          ) : (
            records.map((record) => {
              const link = record.proof_links?.[0];
              const statusLabel = displayStatus(record.status || "planned");
              return (
                <div key={`${record.proposal_id}:${record.milestone_title}`} className="ledger-row">
                  <span className="ledger-cell ledger-primary">
                    {link ? <a href={link}>{record.milestone_title}</a> : <strong>{record.milestone_title}</strong>}
                    <small>{record.proposal_title}</small>
                  </span>
                  <span className="ledger-cell ledger-primary">
                    <strong>{record.workstream || "General"}</strong>
                    <small>{record.proposal_id}</small>
                  </span>
                  <span className="ledger-cell ledger-mono">
                    <span className={badgeClass(record.status || "planned")}>{statusLabel}</span>
                  </span>
                  <span className="ledger-cell ledger-mono">{(record.delivered_at || "pending").slice(0, 10)}</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </section>
  );
}
