import type { HomePageProps, Meta } from "../types";
import { SiteLayout } from "../components/SiteLayout";
import { TimelineFeed } from "../components/TimelineFeed";

export function HomePage({ meta, props }: { meta: Meta; props: HomePageProps }) {
  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel">
        <div>
          <span className="eyebrow">Gnars Atlas</span>
          <h1>{props.hero.title}</h1>
          <p>{props.hero.description}</p>
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
          <span className="eyebrow">Community</span>
          <h2>People as active nodes in the Gnars economy.</h2>
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

      <section className="section-block">
        <div className="section-head">
          <span className="eyebrow">Gnars World</span>
          <h2>Projects and workstreams shaped by treasury, governance, and proof of work.</h2>
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
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Governance Pulse</span>
            <h2>Recent proposals and treasury routes.</h2>
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
        <div>
          <div className="section-head">
            <span className="eyebrow">Now</span>
            <h2>A living chronology of governance and delivery.</h2>
          </div>
          <TimelineFeed items={props.timeline} />
        </div>
      </section>

      <section className="section-block">
        <div className="section-head">
          <span className="eyebrow">Leaderboards</span>
          <h2>Treasury visibility without losing the human layer.</h2>
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
