import { SiteLayout } from "../components/SiteLayout";
import type { Meta, ProposalsPageProps } from "../types";

export function ProposalsPage({ meta, props }: { meta: Meta; props: ProposalsPageProps }) {
  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Governance</span>
          <h1>The readable history of Gnars governance as treasury routing and cultural direction.</h1>
          <p>Every proposal is a social contract, a treasury instruction, and a public signal to the network.</p>
        </div>
      </section>

      <section className="section-block">
        <div className="section-head">
          <span className="eyebrow">{props.signals.label}</span>
          <h2>
            {props.signals.metrics.payout_count} treasury routes, {props.signals.metrics.proposal_count} proposals,{" "}
            {props.signals.metrics.delivery_count} delivery signals.
          </h2>
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
