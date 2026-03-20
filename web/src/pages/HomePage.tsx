import { useDeferredValue, useMemo } from "react";
import { ActivityChart } from "../components/ActivityChart";
import { FeedStream } from "../components/FeedStream";
import { FilterToolbar } from "../components/FilterToolbar";
import { NetworkMap } from "../components/NetworkMap";
import { SiteLayout } from "../components/SiteLayout";
import { formatAmount, formatLabel, formatNumber } from "../lib/format";
import { filterFeed } from "../lib/filtering";
import { useUrlState } from "../lib/urlState";
import type { HomePageProps, Meta } from "../types";

function inWindow(date: string, days: number) {
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) {
    return false;
  }
  return parsed.getTime() >= Date.now() - days * 24 * 60 * 60 * 1000;
}

export function HomePage({ meta, props }: { meta: Meta; props: HomePageProps }) {
  const [filters, setFilters] = useUrlState({
    kind: "all",
    status: "all",
    window: "30d",
    search: "",
  });
  const deferredSearch = useDeferredValue(filters.search);
  const feed = useMemo(
    () => filterFeed(props.feed, { ...filters, search: deferredSearch }).slice(0, 80),
    [deferredSearch, filters, props.feed],
  );
  const windowOptions = useMemo(
    () => [
      { value: "30d", label: "30d", count: props.feed.filter((item) => inWindow(item.date, 30)).length },
      { value: "6m", label: "6m", count: props.feed.filter((item) => inWindow(item.date, 183)).length },
    ],
    [props.feed],
  );

  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact live-hero">
        <div>
          <span className="eyebrow">Live Surface</span>
          <h1>{props.hero.title}</h1>
          <p>{props.hero.description}</p>
        </div>
        <div className="status-rail">
          {props.metrics.map((metric) => (
            <article key={metric.label} className="status-cell">
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.detail}</small>
            </article>
          ))}
        </div>
      </section>

      <FilterToolbar
        searchValue={filters.search}
        searchPlaceholder="search the live feed"
        onSearchChange={(search) => setFilters({ search })}
        groups={[
          {
            label: "Kind",
            value: filters.kind,
            options: props.facets.kind,
            onChange: (kind) => setFilters({ kind }),
          },
          {
            label: "Status",
            value: filters.status,
            options: props.facets.status,
            onChange: (status) => setFilters({ status }),
          },
          {
            label: "Window",
            value: filters.window,
            options: windowOptions,
            onChange: (window) => setFilters({ window }),
          },
        ]}
      />

      <section className="page-main-grid">
        <div className="page-feed-column">
          <div className="section-head compact-head">
            <span className="eyebrow">Live Feed</span>
            <h2>Proposal events, treasury routes, updates, media proof, and community signals in one ordered stream.</h2>
          </div>
          <FeedStream items={feed} />
        </div>

        <aside className="page-side-column">
          <article className="leaderboard-card mini-map-panel">
            <div className="section-head compact-head">
              <span className="eyebrow">Map</span>
              <h2>Treasury at the root, proposals and projects in the middle, people on the edge.</h2>
            </div>
            <NetworkMap scene={props.economicMap} mode="home" />
          </article>

          <article className="leaderboard-card">
            <div className="section-head compact-head">
              <span className="eyebrow">Signal Window</span>
              <h2>{props.signalWindow.label}</h2>
            </div>
            <div className="stack-list compact">
              <article className="mini-row static">
                <span>Active Proposals</span>
                <strong>{props.signalWindow.metrics.active_proposals_now}</strong>
              </article>
              <article className="mini-row static">
                <span>Routed Capital</span>
                <strong>{props.signalWindow.metrics.payouts_by_asset.map((item) => formatAmount(item.symbol, item.amount)).join(" + ") || "0"}</strong>
              </article>
              <article className="mini-row static">
                <span>Delivery Signals</span>
                <strong>{props.signalWindow.metrics.delivery_count}</strong>
              </article>
            </div>
          </article>

          <article className="leaderboard-card">
            <div className="section-head compact-head">
              <span className="eyebrow">Concentration</span>
              <h2>Capital is broad in narrative and narrow in routing.</h2>
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

          <ActivityChart
            scene={props.activity}
            title="Signal Curve"
            detail="Governance, treasury routes, and deliveries on one shared clock."
          />
        </aside>
      </section>

      <section className="section-block dense-two-up">
        <div>
          <div className="section-head compact-head">
            <span className="eyebrow">Top People</span>
            <h2>Operators, athletes, and builders with visible routing and proof.</h2>
          </div>
          <div className="stack-list compact">
            {props.featuredCommunity.map((person) => (
              <a key={person.slug} className="mini-row feed-link" href={person.href}>
                <span>{person.tribes.join(" / ")}</span>
                <strong>{person.displayName}</strong>
              </a>
            ))}
          </div>
        </div>
        <div>
          <div className="section-head compact-head">
            <span className="eyebrow">Category Spend</span>
            <h2>Where routed value clusters by workstream logic.</h2>
          </div>
          <div className="stack-list compact">
            {props.insights.spending_by_category.slice(0, 6).map((row) => (
              <article key={row.category} className="mini-row static">
                <span>{row.route_count} routes</span>
                <strong>
                  {row.category} {row.totals_by_asset.length ? `- ${row.totals_by_asset.map((item) => formatAmount(item.symbol, item.amount)).join(" + ")}` : ""}
                </strong>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section-block dense-three-up">
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
        <article className="leaderboard-card">
          <h3>Proof Coverage</h3>
          <div className="stack-list compact">
            {props.insights.workstream_performance.slice(0, 5).map((project) => (
              <article key={project.project_id} className="mini-row static">
                <span>{project.delivery_count} deliveries</span>
                <strong>
                  {project.name} - {project.proof_coverage_pct ?? 0}%
                </strong>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="section-block dense-two-up">
        <div>
          <div className="section-head compact-head">
            <span className="eyebrow">Field Notes</span>
            <h2>Short editorial annotations translated from the public economic graph.</h2>
          </div>
          <div className="stack-list compact">
            {props.fieldNotes.map((note) => (
              <article key={note.note_id} className="list-card dense-card">
                <div className="timeline-meta">
                  <span>{formatLabel(note.kind)}</span>
                  <span>{note.window_id}</span>
                </div>
                <h3>{note.title}</h3>
                <p>{note.summary}</p>
              </article>
            ))}
          </div>
        </div>
        <div>
          <div className="section-head compact-head">
            <span className="eyebrow">Now</span>
            <h2>{formatNumber(feed.length)} filtered events visible as of {props.analyticsAsOf.slice(0, 10)}.</h2>
          </div>
          <div className="stack-list compact">
            {props.governance.slice(0, 6).map((proposal) => (
              <a key={proposal.archiveId} className="mini-row" href={proposal.href}>
                <span>
                  {formatLabel(proposal.status)} / {formatLabel(proposal.category)}
                </span>
                <strong>{proposal.numberLabel} - {proposal.title}</strong>
              </a>
            ))}
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
