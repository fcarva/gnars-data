import { AssetBars } from "../components/AssetBars";
import { SiteLayout } from "../components/SiteLayout";
import { formatAmount, formatLabel } from "../lib/format";
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
            <span className="tag">{formatLabel(proposal.resolvedStatus || proposal.status)}</span>
            <span className={`tag ${proposal.reconciliation.status === "needs-review" ? "tag-warn" : "tag-ok"}`}>
              {proposal.reconciliation.status === "needs-review" ? "Needs Review" : "Matched"}
            </span>
            <span className="tag">{formatLabel(proposal.category)}</span>
            <span className="tag">{formatLabel(proposal.chain)}</span>
            <span className="tag">{proposal.proposerLabel}</span>
            <span className="tag">{proposal.budgetLabel}</span>
          </div>
        </div>
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Budget File</span>
            <h2>Requested budget, routed value, and proposal semantics.</h2>
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
            <article className="mini-row static">
              <span>Requested</span>
              <strong>{proposal.requestedLabel}</strong>
            </article>
            <article className="mini-row static">
              <span>Routed</span>
              <strong>{proposal.routedLabel}</strong>
            </article>
            <article className="mini-row static">
              <span>Treasury Source</span>
              <strong>{proposal.treasurySourceLabel}</strong>
            </article>
            <article className="mini-row static">
              <span>Transactions</span>
              <strong>{proposal.proposedTransactionsSummary}</strong>
            </article>
            {proposal.relatedProject ? (
              <a className="mini-row" href={proposal.relatedProject.href}>
                <span>Project</span>
                <strong>{proposal.relatedProject.label}</strong>
              </a>
            ) : null}
            {proposal.proposalLinks.map((link) => (
              <a key={link.url} className="mini-row" href={link.url}>
                <span>{formatLabel(link.kind)}</span>
                <strong>{link.label}</strong>
              </a>
            ))}
          </div>
        </div>
        <div>
          <div className="section-head">
            <span className="eyebrow">Why It Passes</span>
            <h2>Argumentation, expected proof, and reconciliation state.</h2>
          </div>
          <div className="stack-list">
            <article className="list-card">
              <div className="timeline-meta">
                <span>Why Vote Yes</span>
                <span>{formatLabel(proposal.reconciliation.resolvedStatus)}</span>
              </div>
              <p>{proposal.whyVoteYes || "No dedicated rationale section was parsed from the proposal body."}</p>
            </article>
            <article className="list-card">
              <div className="timeline-meta">
                <span>Proof Expectations</span>
                <span>{proposal.reconciliation.status}</span>
              </div>
              <p>{proposal.proofExpectations || "No explicit delivery or proof section was found in the parsed proposal text."}</p>
            </article>
            <article className="list-card">
              <div className="timeline-meta">
                <span>Reconciliation</span>
                <span>{proposal.reconciliation.siteStatus} / {proposal.reconciliation.chainStatus}</span>
              </div>
              <div className="stack-list compact">
                <article className="mini-row static">
                  <span>Resolved</span>
                  <strong>{proposal.reconciliation.resolvedStatus}</strong>
                </article>
                {proposal.reconciliation.evidenceUrls.map((url) => (
                  <a key={url} className="mini-row" href={url}>
                    <span>Evidence</span>
                    <strong>{url.replace(/^https?:\/\//, "").slice(0, 52)}</strong>
                  </a>
                ))}
              </div>
            </article>
          </div>
        </div>
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Recipients</span>
            <h2>People or addresses tied to the proposal payload.</h2>
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
        <div>
          <div className="section-head">
            <span className="eyebrow">Contributor Roles</span>
            <h2>People and roles parsed from the proposal or linked workstream.</h2>
          </div>
          <div className="ledger-table compact-ledger">
            <div className="ledger-head">
              <span>Name</span>
              <span>Role</span>
              <span>Budget</span>
            </div>
            <div className="ledger-body">
              {proposal.contributorRoles.length ? (
                proposal.contributorRoles.map((row, index) => (
                  <div key={`${row.name}:${row.role}:${index}`} className="ledger-row">
                    <span className="ledger-cell ledger-primary">
                      <strong>{row.name}</strong>
                    </span>
                    <span className="ledger-cell">{row.role}</span>
                    <span className="ledger-cell ledger-mono">{row.budget || "n/a"}</span>
                  </div>
                ))
              ) : (
                <div className="ledger-empty">
                  <strong>No contributor table parsed.</strong>
                  <span>The linked workstream and recipient list still preserve economic lineage below.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Flow Lineage</span>
            <h2>Fungible treasury routes decoded from proposal payloads.</h2>
          </div>
          <article className="list-card">
            <div className="timeline-meta">
              <span>Treasury Routing</span>
              <span>{proposal.budgetLabel}</span>
            </div>
            <AssetBars items={proposal.flowLineage} emptyLabel="No decoded fungible flows" />
          </article>
        </div>
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
      </section>

      <section className="section-block">
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
      </section>
    </SiteLayout>
  );
}
