import { ActivityChart } from "../components/ActivityChart";
import { AssetBars } from "../components/AssetBars";
import { SiteLayout } from "../components/SiteLayout";
import { TimelineFeed } from "../components/TimelineFeed";
import { formatAmount } from "../lib/format";
import type { CommunityProfilePageProps, Meta } from "../types";

export function CommunityProfilePage({ meta, props }: { meta: Meta; props: CommunityProfilePageProps }) {
  return (
    <SiteLayout meta={meta}>
      <section className="profile-hero">
        <div className="profile-identity">
          <div className="profile-avatar">
            {props.profile.avatarUrl ? <img alt={props.profile.displayName} src={props.profile.avatarUrl} /> : <span>[]</span>}
          </div>
          <div>
            <span className="eyebrow">Community Dossier</span>
            <h1>{props.profile.displayName}</h1>
            <p>{props.profile.bio || props.profile.role}</p>
            <div className="tag-row">
              {props.profile.tribes.map((tribe) => (
                <span key={tribe} className="tag">
                  {tribe}
                </span>
              ))}
              {props.profile.identityLabel !== props.profile.displayName ? (
                <span className="tag muted">{props.profile.identityLabel}</span>
              ) : null}
              <span className={`tag ${props.profile.identityConfidence === "high" ? "tag-ok" : props.profile.identityConfidence === "medium" ? "tag-info" : "tag-warn"}`}>
                {props.profile.identitySource}
              </span>
            </div>
          </div>
        </div>
        <div className="scoreboard">
          <article className="score-card hero">
            <span>Total Received</span>
            <strong>
              {props.economics.totalReceivedPrimary
                ? formatAmount(props.economics.totalReceivedPrimary.symbol, props.economics.totalReceivedPrimary.amount)
                : "0 ETH"}
            </strong>
            <small>Successful treasury outflows tied to this address.</small>
          </article>
          <article className="score-card">
            <span>Approved Proposals</span>
            <strong>{props.economics.approvedProposals}</strong>
            <small>Successful proposals authored by this address.</small>
          </article>
          <article className="score-card">
            <span>Budget Managed</span>
            <strong>
              {props.economics.budgetManagedByAsset.length
                ? props.economics.budgetManagedByAsset.map((item) => formatAmount(item.symbol, item.amount)).join(" + ")
                : "0"}
            </strong>
            <small>Successful budgets led directly or through owned workstreams.</small>
          </article>
        </div>
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Economics</span>
            <h2>Asset receipts, governance posture, and delivery cadence.</h2>
          </div>
          <div className="stack-list">
            <article className="list-card">
              <div className="timeline-meta">
                <span>Receipt Breakdown</span>
                <span>{props.governanceMetrics.deliveryCount} delivery signals</span>
              </div>
              <AssetBars items={props.economics.totalReceivedByAsset} />
            </article>
            <article className="list-card">
              <div className="timeline-meta">
                <span>Governance</span>
                <span>{props.governanceMetrics.proposalSuccessRate}% success rate</span>
              </div>
              <div className="stack-list compact">
                <article className="mini-row static">
                  <span>Authored Split</span>
                  <strong>
                    {props.governanceMetrics.authoredSplit.successful} ok / {props.governanceMetrics.authoredSplit.active} active / {props.governanceMetrics.authoredSplit.closed} closed
                  </strong>
                </article>
                <article className="mini-row static">
                  <span>Active Votes</span>
                  <strong>{props.governanceMetrics.activeVotes}</strong>
                </article>
                <article className="mini-row static">
                  <span>Votes Cast</span>
                  <strong>{props.governanceMetrics.votesCast}</strong>
                </article>
                <article className="mini-row static">
                  <span>Attendance</span>
                  <strong>{props.governanceMetrics.attendancePct ?? "n/a"}%</strong>
                </article>
                <article className="mini-row static">
                  <span>Like Rate</span>
                  <strong>{props.governanceMetrics.likePct ?? "n/a"}%</strong>
                </article>
              </div>
            </article>
            <article className="list-card">
              <div className="timeline-meta">
                <span>Treasury Ledger</span>
                <span>{props.economics.treasuryLedger.length} latest recipient routes</span>
              </div>
              <div className="stack-list compact">
                {props.economics.treasuryLedger.length ? (
                  props.economics.treasuryLedger.map((row) => (
                    <a key={`${row.href}:${row.dateLabel}:${row.amountLabel}`} className="mini-row" href={row.href}>
                      <span>{row.dateLabel} {row.projectLabel ? `/ ${row.projectLabel}` : ""}</span>
                      <strong>{row.proposalLabel} / {row.amountLabel}</strong>
                    </a>
                  ))
                ) : (
                  <article className="mini-row static">
                    <span>Treasury</span>
                    <strong>No successful direct recipient routes yet</strong>
                  </article>
                )}
              </div>
            </article>
          </div>
        </div>
        <ActivityChart
          scene={props.activity}
          title="Profile Signal Curve"
          detail="A compact line of governance, treasury, and delivery around this profile."
        />
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Governance Log</span>
            <h2>Proposals, outcomes, and treasury routing.</h2>
          </div>
          <div className="stack-list">
            {props.governanceLog.length ? (
              props.governanceLog.map((item) => (
                <a key={item.href} className="list-card" href={item.href}>
                  <div className="timeline-meta">
                    <span>{item.numberLabel}</span>
                    <span>{item.status}</span>
                    <span>{item.endedAt}</span>
                  </div>
                  <h3>{item.title}</h3>
                  <p>{item.budgetLabel}</p>
                </a>
              ))
            ) : (
              <article className="list-card">
                <h3>No authored proposals yet</h3>
                <p>This profile is still legible through receipts, votes, workstreams, and public proof.</p>
              </article>
            )}
          </div>
        </div>
        <div>
          <div className="section-head">
            <span className="eyebrow">Proof Of Work</span>
            <h2>Updates, deliveries, and public references.</h2>
          </div>
          <TimelineFeed items={props.proofOfWork} />
        </div>
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Network Neighbors</span>
            <h2>The nearest proposals, projects, and linked community nodes.</h2>
          </div>
          <div className="stack-list compact">
            {props.networkNeighbors.map((item) => (
              <a key={`${item.kind}:${item.href}`} className="mini-row" href={item.href}>
                <span>
                  {item.relationship} / {item.kind}
                </span>
                <strong>
                  {item.label} {item.valueLabel ? `- ${item.valueLabel}` : ""}
                </strong>
              </a>
            ))}
          </div>
        </div>
        <div>
          <div className="section-head">
            <span className="eyebrow">Identity & References</span>
            <h2>Identity provenance, participation, and related workstreams.</h2>
          </div>
          <div className="stack-list compact">
            <article className="mini-row static">
              <span>Identity</span>
              <strong>{props.profile.identitySource} / {props.profile.identityConfidence}</strong>
            </article>
            {props.profile.links.map((link) => (
              <a key={link.url} className="mini-row" href={link.url}>
                <span>{link.kind}</span>
                <strong>{link.label}</strong>
              </a>
            ))}
            {props.projects.map((project) => (
              <a key={project.href} className="mini-row" href={project.href}>
                <span>Project</span>
                <strong>{project.label}</strong>
              </a>
            ))}
            {props.participation.map((item) => (
              <a key={item.href} className="mini-row" href={item.href}>
                <span>{item.status}</span>
                <strong>
                  {item.numberLabel} - {item.title}
                </strong>
              </a>
            ))}
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
