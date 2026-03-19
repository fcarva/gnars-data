import { NetworkMap } from "../components/NetworkMap";
import { SiteLayout } from "../components/SiteLayout";
import type { Meta, NetworkPageProps } from "../types";

export function NetworkPage({ meta, props }: { meta: Meta; props: NetworkPageProps }) {
  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Network</span>
          <h1>The full Gnars economic graph: treasury, proposals, projects, and people.</h1>
          <p>Filter the graph by tribe, asset, and status to read the DAO as a living allocation network.</p>
        </div>
      </section>
      <NetworkMap scene={props.scene} mode="full" />
      <section className="leaderboard-grid">
        {props.highlights.map((group) => (
          <article key={group.title} className="leaderboard-card">
            <h3>{group.title}</h3>
            <div className="stack-list compact">
              {group.items.map((item) => (
                <a key={`${group.title}:${item.href}`} className="mini-row" href={item.href}>
                  <span>{item.detail}</span>
                  <strong>{item.label}</strong>
                </a>
              ))}
            </div>
          </article>
        ))}
      </section>
    </SiteLayout>
  );
}
