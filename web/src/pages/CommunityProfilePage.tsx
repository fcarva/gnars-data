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
            {props.profile.avatarUrl ? <img alt={props.profile.displayName} src={props.profile.avatarUrl} /> : <span>⌐◨-◨</span>}
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
              <span className="tag muted">{props.profile.addressShort}</span>
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
            <small>Canonical treasury outflows from successful governance records.</small>
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
            <small>Successful proposal budgets led or owned through workstreams.</small>
          </article>
        </div>
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
                <p>This profile is still visible through treasury flows, participation, and linked workstreams.</p>
              </article>
            )}
          </div>
        </div>
        <div>
          <div className="section-head">
            <span className="eyebrow">Proof Of Work</span>
            <h2>Updates, deliveries, and verifiable public references.</h2>
          </div>
          <TimelineFeed items={props.proofOfWork} />
        </div>
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Participation</span>
            <h2>Where this address appears across governance.</h2>
          </div>
          <div className="stack-list compact">
            {props.participation.map((item) => (
              <a key={item.href} className="mini-row" href={item.href}>
                <span>
                  {item.numberLabel} - {item.title}
                </span>
                <strong>{item.status}</strong>
              </a>
            ))}
          </div>
        </div>
        <div>
          <div className="section-head">
            <span className="eyebrow">References</span>
            <h2>Identity and related surfaces.</h2>
          </div>
          <div className="stack-list compact">
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
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
