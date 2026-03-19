import { ActivityChart } from "../components/ActivityChart";
import { NetworkMap } from "../components/NetworkMap";
import { SiteLayout } from "../components/SiteLayout";
import { TimelineFeed } from "../components/TimelineFeed";
import type { HomePageProps, Meta } from "../types";

export function HomePage({ meta, props }: { meta: Meta; props: HomePageProps }) {
  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel atlas-hero">
        <div>
          <span className="eyebrow">Economic Map</span>
          <h1>{props.hero.title}</h1>
          <p>{props.hero.description}</p>
          <div className="tag-row">
            <span className="tag">As of {props.asOf.slice(0, 10)}</span>
            <span className="tag">Daily Static</span>
            <span className="tag">Lab + Field</span>
          </div>
        </div>
        <div className="metric-grid">
          {props.metrics.map((metric) => (
            <article key={metric.label} className="metric-card">
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.detail}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="section-block">
        <div className="section-head">
          <span className="eyebrow">Economic Map</span>
          <h2>Treasury at the root, proposals and projects in the middle, people on the edge.</h2>
        </div>
        <NetworkMap scene={props.economicMap} mode="home" />
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Signals</span>
            <h2>Recent activity windows, proposal momentum, and routed capital.</h2>
          </div>
          <div className="signal-grid">
            <article className="list-card">
              <div className="timeline-meta">
                <span>{props.signalWindow.label}</span>
                <span>{props.signalWindow.metrics.active_proposals_now} active now</span>
              </div>
              <h3>{props.signalWindow.metrics.payout_count} treasury routes</h3>
              <p>
                {props.signalWindow.metrics.payouts_by_asset.map((item) => `${item.amount} ${item.symbol}`).join(" + ")} routed
                across {props.signalWindow.metrics.recipient_count} recipients and {props.signalWindow.metrics.delivery_count} delivery signals.
              </p>
            </article>
            <article className="leaderboard-card">
              <h3>Top Recipients</h3>
              <div className="stack-list compact">
                {props.signalWindow.top_recipients.slice(0, 5).map((item) => (
                  <article key={item.address} className="mini-row static">
                    <span>{item.totals_by_asset.map((asset) => `${asset.amount} ${asset.symbol}`).join(" + ")}</span>
                    <strong>{item.display_name}</strong>
                  </article>
                ))}
              </div>
            </article>
            <article className="leaderboard-card">
              <h3>Top Projects</h3>
              <div className="stack-list compact">
                {props.signalWindow.top_projects.slice(0, 5).map((item) => (
                  <article key={item.project_id} className="mini-row static">
                    <span>{item.totals_by_asset.map((asset) => `${asset.amount} ${asset.symbol}`).join(" + ")}</span>
                    <strong>{item.project_name}</strong>
                  </article>
                ))}
              </div>
            </article>
          </div>
        </div>
        <ActivityChart
          scene={props.activity}
          title="Daily Signal Curve"
          detail="Governance events, treasury routes, and delivery proofs on one shared timeline."
        />
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Field Notes</span>
            <h2>Editorial annotations for the public economic graph.</h2>
          </div>
          <div className="stack-list">
            {props.fieldNotes.map((note) => (
              <article key={note.note_id} className="list-card">
                <div className="timeline-meta">
                  <span>{note.kind}</span>
                  <span>{note.window_id}</span>
                </div>
                <h3>{note.title}</h3>
                <p>{note.summary}</p>
              </article>
            ))}
          </div>
        </div>
        <div>
          <div className="section-head">
            <span className="eyebrow">Now</span>
            <h2>A living chronology of proposals, payouts, and public proof.</h2>
          </div>
          <TimelineFeed items={props.timeline} />
        </div>
      </section>

      <section className="section-block">
        <div className="section-head">
          <span className="eyebrow">Community</span>
          <h2>Profiles as economic nodes with governance history and treasury lineage.</h2>
        </div>
        <div className="dense-grid">
          {props.featuredCommunity.map((person) => (
            <a key={person.slug} className="feature-card" href={person.href}>
              <div className="tag-row">
                {person.tribes.map((tribe) => (
                  <span key={tribe} className="tag">
                    {tribe}
                  </span>
                ))}
              </div>
              <h3>{person.displayName}</h3>
              <p>{person.subtitle}</p>
              <div className="feature-stats">
                <span>{person.totalReceivedLabel}</span>
                <span>{person.approvedProposals} passed</span>
                <span>{person.budgetManagedLabel}</span>
              </div>
            </a>
          ))}
        </div>
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Gnars World</span>
            <h2>Projects are treated as delivery systems, not portfolio thumbnails.</h2>
          </div>
          <div className="masonry-grid">
            {props.featuredProjects.map((project) => (
              <a key={project.id} className="project-card" href={project.href}>
                <span className="project-status">{project.status}</span>
                <h3>{project.title}</h3>
                <p>{project.summary}</p>
                <div className="project-meta">
                  <span>{project.category}</span>
                  <span>{project.proposalTag}</span>
                  <span>{project.budgetLabel}</span>
                </div>
              </a>
            ))}
          </div>
        </div>
        <div>
          <div className="section-head">
            <span className="eyebrow">Governance Pulse</span>
            <h2>Proposal history as a routing layer for capital and labor.</h2>
          </div>
          <div className="stack-list">
            {props.governance.map((proposal) => (
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
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>

      <section className="section-block">
        <div className="section-head">
          <span className="eyebrow">Leaderboards</span>
          <h2>Read treasury concentration without losing the human layer.</h2>
        </div>
        <div className="leaderboard-grid">
          {props.leaderboards.map((board) => (
            <article key={board.title} className="leaderboard-card">
              <h3>{board.title}</h3>
              <div className="stack-list compact">
                {board.items.map((item) => (
                  <a key={item.href} className="mini-row" href={item.href}>
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                  </a>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </SiteLayout>
  );
}
