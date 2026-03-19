import { useState } from "react";
import { AssetBars } from "../components/AssetBars";
import { SankeyChart } from "../components/SankeyChart";
import { SiteLayout } from "../components/SiteLayout";
import type { Meta, TreasuryPageProps } from "../types";

export function TreasuryPage({ meta, props }: { meta: Meta; props: TreasuryPageProps }) {
  const [tab, setTab] = useState<"overview" | "flows" | "categories" | "recipients">("overview");
  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Treasury</span>
          <h1>Allocation patterns, recipient concentration, and routed capital across the Gnars treasury.</h1>
          <p>Read treasury activity as a set of linked windows: treasury to proposal, proposal to project, project to recipient.</p>
        </div>
      </section>

      <div className="filter-row">
        {[
          { value: "overview", label: "Overview" },
          { value: "flows", label: "Flows" },
          { value: "categories", label: "Categories" },
          { value: "recipients", label: "Recipients" },
        ].map((item) => (
          <button
            key={item.value}
            type="button"
            className={tab === item.value ? "filter-pill is-active" : "filter-pill"}
            onClick={() => setTab(item.value as typeof tab)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === "overview" ? (
        <section className="dense-two-up">
          <article className="leaderboard-card">
            <div className="section-head compact-head">
              <span className="eyebrow">Current Breakdown</span>
              <h2>Treasury holdings by asset.</h2>
            </div>
            <AssetBars items={props.insights.treasury_breakdown.assets.map((item) => ({ symbol: item.symbol, amount: item.value_usd }))} emptyLabel="No assets" />
          </article>
          <article className="leaderboard-card">
            <div className="section-head compact-head">
              <span className="eyebrow">Recipient Concentration</span>
              <h2>How much routing is clustered in the top addresses.</h2>
            </div>
            <div className="stack-list compact">
              {props.insights.recipient_concentration.map((asset) => (
                <article key={asset.symbol} className="mini-row static">
                  <span>{asset.symbol}</span>
                  <strong>{asset.top10_share_pct ?? 0}% top-10 share</strong>
                </article>
              ))}
            </div>
          </article>
        </section>
      ) : null}

      {tab === "flows" ? <SankeyChart view={props.treasuryScene} /> : null}

      {tab === "categories" ? (
        <section className="stack-list compact">
          {props.insights.spending_by_category.map((row) => (
            <article key={row.category} className="list-card dense-card">
              <div className="timeline-meta">
                <span>{row.route_count} routes</span>
                <span>{row.proposal_count} proposals</span>
              </div>
              <h3>{row.category}</h3>
              <AssetBars items={row.totals_by_asset} emptyLabel="No routed value" />
            </article>
          ))}
        </section>
      ) : null}

      {tab === "recipients" ? (
        <section className="dense-two-up">
          {props.insights.recipient_concentration.map((asset) => (
            <article key={asset.symbol} className="leaderboard-card">
              <h3>{asset.symbol}</h3>
              <div className="stack-list compact">
                {asset.top_recipients.map((recipient) => (
                  <a key={`${asset.symbol}:${recipient.slug}`} className="mini-row" href={`/community/${recipient.slug}/`}>
                    <span>{recipient.amount}</span>
                    <strong>{recipient.display_name}</strong>
                  </a>
                ))}
              </div>
            </article>
          ))}
        </section>
      ) : null}

      <section className="section-block dense-two-up">
        <div>
          <div className="section-head compact-head">
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
          <div className="section-head compact-head">
            <span className="eyebrow">Proposal Routes</span>
            <h2>Decoded treasury lineage by proposal.</h2>
          </div>
          <div className="stack-list compact">
            {props.proposalRoutes.slice(0, 10).map((route) => (
              <a key={route.archive_id} className="list-card dense-card" href={`/proposals/${route.archive_id}/`}>
                <div className="timeline-meta">
                  <span>{route.proposal_number !== null ? `Prop #${route.proposal_number}` : route.archive_id}</span>
                  <span>{route.proposal_status}</span>
                </div>
                <h3>{route.proposal_title}</h3>
                <AssetBars items={route.totals_by_asset} emptyLabel="No routed value" />
              </a>
            ))}
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
