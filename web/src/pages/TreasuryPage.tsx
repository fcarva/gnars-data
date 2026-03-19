import { AssetBars } from "../components/AssetBars";
import { SankeyChart } from "../components/SankeyChart";
import { SiteLayout } from "../components/SiteLayout";
import type { Meta, TreasuryPageProps } from "../types";

export function TreasuryPage({ meta, props }: { meta: Meta; props: TreasuryPageProps }) {
  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Treasury</span>
          <h1>Allocation patterns, routed capital, and recipient views across the Gnars treasury.</h1>
          <p>The treasury page reads governance payloads as flows: treasury to proposal, proposal to project, project to recipient.</p>
        </div>
      </section>
      <SankeyChart view={props.treasuryScene} />
      <section className="section-block two-up">
        <div>
          <div className="section-head">
            <span className="eyebrow">Windows</span>
            <h2>Recent and all-time treasury routing windows.</h2>
          </div>
          <div className="stack-list compact">
            {props.windows.map((window) => (
              <article key={window.window_id} className="mini-row static">
                <span>{window.totals_by_asset.map((item) => `${item.amount} ${item.symbol}`).join(" + ")}</span>
                <strong>
                  {window.label} / {window.route_count} routes / {window.recipient_count} recipients
                </strong>
              </article>
            ))}
          </div>
        </div>
        <div>
          <div className="section-head">
            <span className="eyebrow">Proposal Routes</span>
            <h2>Decoded treasury lineage by proposal.</h2>
          </div>
          <div className="stack-list">
            {props.proposalRoutes.slice(0, 10).map((route) => (
              <article key={route.archive_id} className="list-card">
                <div className="timeline-meta">
                  <span>{route.proposal_number !== null ? `Prop #${route.proposal_number}` : route.archive_id}</span>
                  <span>{route.proposal_status}</span>
                </div>
                <h3>{route.proposal_title}</h3>
                <AssetBars items={route.totals_by_asset} emptyLabel="No routed value" />
              </article>
            ))}
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
