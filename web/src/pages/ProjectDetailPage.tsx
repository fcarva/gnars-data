import { SiteLayout } from "../components/SiteLayout";
import { TimelineFeed } from "../components/TimelineFeed";
import { formatAmount } from "../lib/format";
import type { Meta, ProjectDetailPageProps } from "../types";

export function ProjectDetailPage({ meta, props }: { meta: Meta; props: ProjectDetailPageProps }) {
  const { project } = props;
  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Project Dossier</span>
          <h1>{project.title}</h1>
          <p>{project.objective}</p>
          <div className="tag-row">
            <span className="tag">{project.status}</span>
            <span className="tag">{project.category}</span>
            <span className="tag">{project.proposalTag}</span>
          </div>
        </div>
      </section>

      <div className="scoreboard compact">
        <article className="score-card">
          <span>Approved Budget</span>
          <strong>{project.budgetByAsset.map((item) => formatAmount(item.symbol, item.amount)).join(" + ") || "0"}</strong>
        </article>
        <article className="score-card">
          <span>Spent</span>
          <strong>{project.spentByAsset.map((item) => formatAmount(item.symbol, item.amount)).join(" + ") || "0"}</strong>
        </article>
        <article className="score-card">
          <span>Utilization</span>
          <strong>{project.utilization.map((item) => item.value).join(" - ") || "n/a"}</strong>
        </article>
      </div>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Outputs</span>
            <h2>What this workstream aims to deliver.</h2>
          </div>
          <div className="stack-list compact">
            {project.outputs.map((item) => (
              <article key={item} className="mini-row static">
                <span>Output</span>
                <strong>{item}</strong>
              </article>
            ))}
            {project.kpis.map((item) => (
              <article key={item} className="mini-row static">
                <span>KPI</span>
                <strong>{item}</strong>
              </article>
            ))}
          </div>
        </div>
        <div>
          <div className="section-head">
            <span className="eyebrow">Recipients</span>
            <h2>Who handled the budget.</h2>
          </div>
          <div className="stack-list compact">
            {project.recipients.map((recipient) => (
              <a key={recipient.href} className="mini-row" href={recipient.href}>
                <span>{recipient.amounts.map((item) => formatAmount(item.symbol, item.amount)).join(" + ")}</span>
                <strong>{recipient.label}</strong>
              </a>
            ))}
          </div>
        </div>
      </section>

      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Related Proposals</span>
            <h2>Governance links that created or shaped this workstream.</h2>
          </div>
          <div className="stack-list compact">
            {project.proposalLinks.map((proposal) => (
              <a key={proposal.href} className="mini-row" href={proposal.href}>
                <span>Proposal</span>
                <strong>{proposal.label}</strong>
              </a>
            ))}
          </div>
        </div>
        <div>
          <div className="section-head">
            <span className="eyebrow">Proof Of Work</span>
            <h2>Chronology of updates and public checkpoints.</h2>
          </div>
          <TimelineFeed items={project.timeline} />
        </div>
      </section>
    </SiteLayout>
  );
}
