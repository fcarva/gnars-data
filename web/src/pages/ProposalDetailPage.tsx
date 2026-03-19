import { SiteLayout } from "../components/SiteLayout";
import { formatAmount } from "../lib/format";
import type { Meta, ProposalDetailPageProps } from "../types";

export function ProposalDetailPage({ meta, props }: { meta: Meta; props: ProposalDetailPageProps }) {
  const { proposal } = props;
  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">{proposal.numberLabel}</span>
          <h1>{proposal.title}</h1>
          <p>{proposal.contentSummary}</p>
          <div className="tag-row">
            <span className="tag">{proposal.status}</span>
            <span className="tag">{proposal.proposerLabel}</span>
            <span className="tag">{proposal.budgetLabel}</span>
          </div>
        </div>
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Proposal File</span>
            <h2>Timing, routing, and links.</h2>
          </div>
          <div className="stack-list compact">
            <article className="mini-row static">
              <span>Created</span>
              <strong>{proposal.createdAt}</strong>
            </article>
            <article className="mini-row static">
              <span>Ended</span>
              <strong>{proposal.endAt}</strong>
            </article>
            {proposal.relatedProject ? (
              <a className="mini-row" href={proposal.relatedProject.href}>
                <span>Project</span>
                <strong>{proposal.relatedProject.label}</strong>
              </a>
            ) : null}
            {proposal.proposalLinks.map((link) => (
              <a key={link.url} className="mini-row" href={link.url}>
                <span>{link.kind}</span>
                <strong>{link.label}</strong>
              </a>
            ))}
          </div>
        </div>
        <div>
          <div className="section-head">
            <span className="eyebrow">Treasury Routing</span>
            <h2>Recipients tied to the proposal payload.</h2>
          </div>
          <div className="stack-list compact">
            {proposal.recipients.length ? (
              proposal.recipients.map((recipient) =>
                recipient.href ? (
                  <a key={`${recipient.label}:${recipient.href}`} className="mini-row" href={recipient.href}>
                    <span>{recipient.amounts.map((item) => formatAmount(item.symbol, item.amount)).join(" + ")}</span>
                    <strong>{recipient.label}</strong>
                  </a>
                ) : (
                  <article key={recipient.label} className="mini-row static">
                    <span>{recipient.amounts.map((item) => formatAmount(item.symbol, item.amount)).join(" + ")}</span>
                    <strong>{recipient.label}</strong>
                  </article>
                ),
              )
            ) : (
              <article className="mini-row static">
                <span>Treasury</span>
                <strong>No decoded fungible flows</strong>
              </article>
            )}
          </div>
        </div>
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Related People</span>
            <h2>Who authored or received value through this proposal.</h2>
          </div>
          <div className="stack-list compact">
            {proposal.relatedPeople.map((person) => (
              <a key={person.href} className="mini-row" href={person.href}>
                <span>Community</span>
                <strong>{person.label}</strong>
              </a>
            ))}
          </div>
        </div>
        <div>
          <div className="section-head">
            <span className="eyebrow">Choice Set</span>
            <h2>How the proposal was structured for voting.</h2>
          </div>
          <div className="stack-list compact">
            {proposal.choices.map((choice, index) => (
              <article key={`${choice}:${index}`} className="mini-row static">
                <span>{proposal.scoresByChoice[index] ?? 0} votes</span>
                <strong>{choice}</strong>
              </article>
            ))}
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
