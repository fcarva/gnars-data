import { SiteLayout } from "../components/SiteLayout";
import type { Meta, ProposalsPageProps } from "../types";

export function ProposalsPage({ meta, props }: { meta: Meta; props: ProposalsPageProps }) {
  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Governance</span>
          <h1>The readable history of Gnars governance.</h1>
          <p>Every proposal is shown as a treasury instruction, a social contract, and a community event.</p>
        </div>
      </section>
      <section className="stack-list">
        {props.proposals.map((proposal) => (
          <a key={proposal.archiveId} className="list-card" href={proposal.href}>
            <div className="timeline-meta">
              <span>{proposal.numberLabel}</span>
              <span>{proposal.status}</span>
            </div>
            <h3>{proposal.title}</h3>
            <p>{proposal.summary}</p>
            <div className="feature-stats">
              <span>{proposal.proposerLabel}</span>
              <span>{proposal.budgetLabel}</span>
              {proposal.projectLabel ? <span>{proposal.projectLabel}</span> : null}
            </div>
          </a>
        ))}
      </section>
    </SiteLayout>
  );
}
