import { useDeferredValue, useMemo } from "react";
import { AssetBars } from "../components/AssetBars";
import { FilterToolbar } from "../components/FilterToolbar";
import { SankeyChart } from "../components/SankeyChart";
import { SiteLayout } from "../components/SiteLayout";
import { filterTreasuryProposalRows, filterTreasuryRoutes } from "../lib/filtering";
import { formatAmount, formatAssetSymbol, formatDate, formatLabel, formatNumber } from "../lib/format";
import { useUrlState } from "../lib/urlState";
import type { AssetAmount, Meta, TreasuryPageProps } from "../types";

type AssetTotalRow = {
  symbol: string;
  amount: number;
  tokenContract?: string | null;
};

const PRIMARY_ASSETS = new Set(["USDC", "ETH", "GNARS", "SENDIT"]);

function sumAssets(items: { assetSymbol: string; amount: number; tokenContract?: string | null }[]): AssetTotalRow[] {
  const totals = new Map<string, { amount: number; tokenContract?: string | null }>();
  for (const item of items) {
    const current = totals.get(item.assetSymbol) ?? { amount: 0, tokenContract: item.tokenContract ?? null };
    current.amount += item.amount;
    if (!current.tokenContract && item.tokenContract) {
      current.tokenContract = item.tokenContract;
    }
    totals.set(item.assetSymbol, current);
  }
  return [...totals.entries()]
    .map(([symbol, value]) => ({
      symbol,
      amount: Number(value.amount.toFixed(8)),
      tokenContract: value.tokenContract ?? null,
    }))
    .sort((left, right) => right.amount - left.amount || left.symbol.localeCompare(right.symbol));
}

function describeAssetMix(items: AssetTotalRow[]): string {
  if (!items.length) {
    return "0";
  }
  if (items.length === 1) {
    return formatAmount(items[0].symbol, items[0].amount, items[0].tokenContract);
  }

  const primary = items.filter((item) => PRIMARY_ASSETS.has(item.symbol.toUpperCase()));
  const longTail = items.filter((item) => !PRIMARY_ASSETS.has(item.symbol.toUpperCase()));
  const visible = (primary.length ? primary : items).slice(0, 2);
  const parts = visible.map((item) => formatAmount(item.symbol, item.amount, item.tokenContract));
  if (longTail.length) {
    parts.push(`${longTail.length} other token ${longTail.length === 1 ? "lane" : "lanes"}`);
  } else if (items.length > visible.length) {
    parts.push(`${items.length - visible.length} more assets`);
  }
  return parts.join(" + ");
}

function latestRouteAt(routes: { eventAt: string }[]): string | null {
  if (!routes.length) {
    return null;
  }
  return routes.reduce((latest, route) => (route.eventAt > latest ? route.eventAt : latest), routes[0].eventAt);
}

function daysSince(value: string | null): number | null {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return Math.floor((Date.now() - parsed.getTime()) / (1000 * 60 * 60 * 24));
}

function reconciliationTone(status: string): string {
  switch (status) {
    case "matched":
      return "tag-ok";
    case "needs-review":
      return "tag-warn";
    default:
      return "tag-info";
  }
}

export function TreasuryPage({ meta, props }: { meta: Meta; props: TreasuryPageProps }) {
  const defaultWindow = props.windows.find((item) => item.route_count > 0)?.window_id ?? "all";
  const [filters, setFilters] = useUrlState({
    tab: "overview",
    window: defaultWindow,
    asset: "all",
    status: "all",
    category: "all",
    chain: "all",
    search: "",
    sort: "amount_desc",
  });
  const deferredSearch = useDeferredValue(filters.search);
  const routes = useMemo(
    () => filterTreasuryRoutes(props.routes, { ...filters, search: deferredSearch }),
    [deferredSearch, filters, props.routes],
  );
  const proposalRows = useMemo(
    () => filterTreasuryProposalRows(props.proposalRows, { ...filters, search: deferredSearch }),
    [deferredSearch, filters, props.proposalRows],
  );
  const proposalRowByArchiveId = useMemo(
    () => new Map(props.proposalRows.map((row) => [row.archiveId, row])),
    [props.proposalRows],
  );
  const visibleRouteIds = useMemo(() => new Set(routes.map((route) => route.routeId)), [routes]);
  const visibleTreasuryReconciliation = useMemo(
    () => props.treasuryReconciliation.records.filter((record) => visibleRouteIds.has(record.route_id)),
    [props.treasuryReconciliation.records, visibleRouteIds],
  );
  const visibleProposalReconciliation = useMemo(
    () =>
      props.proposalReconciliation.records.filter((record) => {
        const proposalRow = proposalRowByArchiveId.get(record.archive_id);
        if (!proposalRow) {
          return false;
        }
        if (filters.status !== "all" && proposalRow.statusKey !== filters.status) {
          return false;
        }
        if (filters.category !== "all" && proposalRow.categoryKey !== filters.category) {
          return false;
        }
        if (filters.chain !== "all" && proposalRow.proposalChain !== filters.chain) {
          return false;
        }
        const haystack = `${record.title} ${record.site_status} ${record.chain_status} ${proposalRow.searchText}`.toLowerCase();
        return !deferredSearch || haystack.includes(deferredSearch.toLowerCase());
      }),
    [deferredSearch, filters.category, filters.chain, filters.status, proposalRowByArchiveId, props.proposalReconciliation.records],
  );
  const visibleContractReconciliation = useMemo(
    () =>
      props.contractReconciliation.records.filter((record) => {
        if (filters.chain !== "all" && record.network.toLowerCase() !== filters.chain.toLowerCase()) {
          return false;
        }
        const haystack = `${record.contract_id} ${record.label} ${record.kind} ${record.address} ${record.network} ${record.reconciliation_status}`.toLowerCase();
        return !deferredSearch || haystack.includes(deferredSearch.toLowerCase());
      }),
    [deferredSearch, filters.chain, props.contractReconciliation.records],
  );

  const routeTotals = useMemo(
    () =>
      sumAssets(
        routes.map((route) => ({
          assetSymbol: route.assetSymbol,
          amount: route.amount,
          tokenContract: route.tokenContract,
        })),
      ),
    [routes],
  );

  const routeSummary = useMemo(() => {
    const proposalIds = new Set<string>();
    const recipientIds = new Set<string>();
    const projectIds = new Set<string>();
    const recipients = new Map<
      string,
      {
        label: string;
        secondaryLabel: string;
        href: string | null;
        identityStatus: string;
        totals: Map<string, { amount: number; tokenContract?: string | null }>;
        routeCount: number;
        proposalCount: Set<string>;
        projectCount: Set<string>;
        lastSeen: string;
      }
    >();
    const categories = new Map<
      string,
      {
        label: string;
        totals: Map<string, { amount: number; tokenContract?: string | null }>;
        routeCount: number;
        proposalCount: Set<string>;
        recipientCount: Set<string>;
      }
    >();

    for (const route of routes) {
      proposalIds.add(route.proposalHref);
      recipientIds.add(route.recipientHref ?? route.recipientAddress);
      if (route.projectHref) {
        projectIds.add(route.projectHref);
      }

      const recipientKey = route.recipientHref ?? route.recipientAddress;
      const recipientRow = recipients.get(recipientKey) ?? {
        label: route.recipientLabel,
        secondaryLabel: route.recipientSecondaryLabel,
        href: route.recipientHref,
        identityStatus: route.recipientIdentityStatus,
        totals: new Map<string, { amount: number; tokenContract?: string | null }>(),
        routeCount: 0,
        proposalCount: new Set<string>(),
        projectCount: new Set<string>(),
        lastSeen: route.eventAt,
      };
      const recipientAsset = recipientRow.totals.get(route.assetSymbol) ?? { amount: 0, tokenContract: route.tokenContract };
      recipientAsset.amount += route.amount;
      if (!recipientAsset.tokenContract && route.tokenContract) {
        recipientAsset.tokenContract = route.tokenContract;
      }
      recipientRow.totals.set(route.assetSymbol, recipientAsset);
      recipientRow.routeCount += 1;
      recipientRow.proposalCount.add(route.proposalHref);
      if (route.projectHref) {
        recipientRow.projectCount.add(route.projectHref);
      }
      if (route.eventAt > recipientRow.lastSeen) {
        recipientRow.lastSeen = route.eventAt;
      }
      recipients.set(recipientKey, recipientRow);

      const categoryRow = categories.get(route.categoryKey) ?? {
        label: route.category,
        totals: new Map<string, { amount: number; tokenContract?: string | null }>(),
        routeCount: 0,
        proposalCount: new Set<string>(),
        recipientCount: new Set<string>(),
      };
      const categoryAsset = categoryRow.totals.get(route.assetSymbol) ?? { amount: 0, tokenContract: route.tokenContract };
      categoryAsset.amount += route.amount;
      if (!categoryAsset.tokenContract && route.tokenContract) {
        categoryAsset.tokenContract = route.tokenContract;
      }
      categoryRow.totals.set(route.assetSymbol, categoryAsset);
      categoryRow.routeCount += 1;
      categoryRow.proposalCount.add(route.proposalHref);
      categoryRow.recipientCount.add(recipientKey);
      categories.set(route.categoryKey, categoryRow);
    }

    const recipientRows = [...recipients.values()]
      .map((row) => {
        const totalsByAsset = [...row.totals.entries()]
          .map(([symbol, value]) => ({ symbol, amount: value.amount, tokenContract: value.tokenContract ?? null }))
          .sort((left, right) => right.amount - left.amount);
        return {
          ...row,
          totalsByAsset,
          primaryAmount: totalsByAsset.reduce((total, item) => total + item.amount, 0),
        };
      })
      .sort((left, right) => right.primaryAmount - left.primaryAmount || left.label.localeCompare(right.label));

    const categoryRows = [...categories.values()]
      .map((row) => {
        const totalsByAsset = [...row.totals.entries()]
          .map(([symbol, value]) => ({ symbol, amount: value.amount, tokenContract: value.tokenContract ?? null }))
          .sort((left, right) => right.amount - left.amount);
        return {
          ...row,
          totalsByAsset,
          primaryAmount: totalsByAsset.reduce((total, item) => total + item.amount, 0),
        };
      })
      .sort((left, right) => right.primaryAmount - left.primaryAmount || left.label.localeCompare(right.label));

    const top10Share =
      recipientRows.length > 0
        ? Number(
            (
              (recipientRows.slice(0, 10).reduce((total, row) => total + row.primaryAmount, 0) /
                Math.max(1, recipientRows.reduce((total, row) => total + row.primaryAmount, 0))) *
              100
            ).toFixed(1),
          )
        : 0;

    return {
      proposalCount: proposalIds.size,
      recipientCount: recipientIds.size,
      projectCount: projectIds.size,
      recipientRows,
      categoryRows,
      top10Share,
    };
  }, [routes]);

  const activeWindow =
    props.windows.find((item) => item.window_id === filters.window) ??
    props.windows.find((item) => item.window_id === defaultWindow) ??
    props.windows[0];
  const holdingsBars = props.insights.treasury_breakdown.assets.map((item) => ({
    symbol: item.symbol,
    amount: item.value_usd,
  }));
  const routedProposalRows = proposalRows.filter((row) => !row.zeroRoute);
  const zeroRouteRows = proposalRows.filter((row) => row.zeroRoute);
  const routedSummaryLabel = describeAssetMix(routeTotals);
  const concentrationLabel = filters.asset === "all" || routeTotals.length !== 1 ? "Asset-mixed" : `${routeSummary.top10Share}%`;
  const concentrationDetail =
    filters.asset === "all" || routeTotals.length !== 1
      ? "filter a single asset for a defensible concentration read"
      : "top-10 recipient share";
  const asOfLabel = formatDate(props.insights.as_of);
  const lastRoute = latestRouteAt(props.routes);
  const lastRouteLabel = lastRoute ? formatDate(lastRoute) : "No routed history";
  const inactiveDays = daysSince(lastRoute);
  const projectLinkedCount = routes.filter((route) => route.routeKind === "project-linked").length;
  const directRouteCount = Math.max(0, routes.length - projectLinkedCount);
  const quietRecentWindows = props.windows.filter((window) => window.window_id !== "all" && window.route_count === 0).length;
  const coreConcentration = props.insights.recipient_concentration.filter((row) => row.total_amount > 0);
  const reconciliationSummary = props.treasuryReconciliation.summary;
  const isOverview = filters.tab === "overview";
  const showFlows = isOverview || filters.tab === "flows";
  const showCategories = isOverview || filters.tab === "categories";
  const showRecipients = isOverview || filters.tab === "recipients";
  const showReconciliation = filters.tab === "reconciliation";

  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact treasury-hero">
        <div>
          <span className="eyebrow">Treasury</span>
          <h1>Treasury routing, recipient concentration, and proposal lineage in one operating surface.</h1>
          <p>
            Read Gnars treasury as a public routing ledger. Holdings are one layer, decoded outflows are another, and the useful
            read is how proposals route capital into people, categories, and delivered work.
          </p>
        </div>
      </section>

      <section className="status-rail treasury-status-rail">
        <article className="status-cell">
          <small>As Of</small>
          <strong>{asOfLabel}</strong>
          <span>static daily treasury build</span>
        </article>
        <article className="status-cell">
          <small>Window</small>
          <strong>{activeWindow?.label ?? "All Time"}</strong>
          <span>{filters.chain === "all" ? "all chains" : filters.chain}</span>
        </article>
        <article className="status-cell">
          <small>Treasury Now</small>
          <strong>${Math.round(props.insights.treasury_breakdown.assets.reduce((total, asset) => total + asset.value_usd, 0)).toLocaleString("en-US")}</strong>
          <span>{props.insights.treasury_breakdown.assets.length} tracked assets</span>
        </article>
        <article className="status-cell">
          <small>Filtered Routed</small>
          <strong>{routedSummaryLabel}</strong>
          <span>{routes.length} decoded transfers</span>
        </article>
        <article className="status-cell">
          <small>Last Routed</small>
          <strong>{lastRouteLabel}</strong>
          <span>{inactiveDays !== null ? `${inactiveDays} days since last decoded route` : "no cadence signal yet"}</span>
        </article>
        <article className="status-cell">
          <small>Top-10 Share</small>
          <strong>{concentrationLabel}</strong>
          <span>{concentrationDetail}</span>
        </article>
      </section>

      <div className="filter-row tight section-anchor-row">
        {[
          ["overview", "Overview"],
          ["flows", "Flows"],
          ["categories", "Categories"],
          ["recipients", "Recipients"],
          ["reconciliation", "Reconciliation"],
        ].map(([value, label]) => (
          <button
            key={value}
            type="button"
            className={filters.tab === value ? "filter-pill is-active" : "filter-pill"}
            onClick={() => setFilters({ tab: value })}
          >
            {label}
          </button>
        ))}
      </div>

      <FilterToolbar
        searchValue={filters.search}
        searchPlaceholder="search proposals, ENS, recipients, proposers, projects, token contracts, wallet addresses"
        onSearchChange={(search) => setFilters({ search })}
        selectValue={filters.sort}
        selectOptions={[
          { value: "amount_desc", label: "Largest route" },
          { value: "date_desc", label: "Recent route" },
          { value: "recipient_asc", label: "Recipient" },
          { value: "proposal_asc", label: "Proposal" },
        ]}
        onSelectChange={(sort) => setFilters({ sort })}
        groups={[
          {
            label: "Window",
            value: filters.window,
            options: props.windows
              .filter((window) => window.window_id !== "all")
              .map((window) => ({ value: window.window_id, label: window.label, count: window.route_count })),
            onChange: (window) => setFilters({ window }),
          },
          {
            label: "Asset",
            value: filters.asset,
            options: props.facets.asset,
            onChange: (asset) => setFilters({ asset }),
          },
          {
            label: "Status",
            value: filters.status,
            options: props.facets.status,
            onChange: (status) => setFilters({ status }),
          },
          {
            label: "Category",
            value: filters.category,
            options: props.facets.category,
            onChange: (category) => setFilters({ category }),
          },
          {
            label: "Chain",
            value: filters.chain,
            options: props.facets.chain ?? [],
            onChange: (chain) => setFilters({ chain }),
          },
        ]}
      />

      <div className="treasury-note-box treasury-quality-box">
        <strong>Use this page as current holdings plus decoded all-time routing, not as a live ops ticker.</strong>
        <span>
          {quietRecentWindows >= 3
            ? "The recent 7d / 30d / 90d routing windows are empty, so the strongest read here is lineage, concentration, and category allocation across all decoded routes."
            : "The strongest read here is proposal to recipient routing, with project linkage shown only when the route is actually tied to a project record."}
        </span>
      </div>

      {showFlows ? <section className="section-block dense-two-up treasury-main-grid" id="flow-ledger">
        <article className="leaderboard-card treasury-ledger-card">
          <div className="section-head compact-head">
            <span className="eyebrow">Route Ledger</span>
            <h2>{routes.length} decoded routes in the current filter state.</h2>
          </div>
          <div className="ledger-table">
            <div className="ledger-head">
              <span>Date</span>
              <span>Proposal</span>
              <span>Recipient</span>
              <span>Asset</span>
              <span>Amount</span>
            </div>
            <div className="ledger-body">
              {routes.slice(0, 28).map((route) => (
                <div key={route.routeId} className="ledger-row">
                  <span className="ledger-cell ledger-mono">{route.dateLabel}</span>
                  <span className="ledger-cell ledger-primary">
                    <a href={route.proposalHref}>{route.proposalNumberLabel}</a>
                    <small>{route.proposalTitle}</small>
                    <small>{route.proposalStatus} / {route.category} / {route.proposalChain}</small>
                    <small>
                      Proposer · {route.proposerHref ? <a href={route.proposerHref}>{route.proposerLabel}</a> : route.proposerLabel}
                    </small>
                  </span>
                  <span className="ledger-cell ledger-primary">
                    {route.recipientHref ? <a href={route.recipientHref}>{route.recipientLabel}</a> : <strong>{route.recipientLabel}</strong>}
                    <small>{route.recipientSecondaryLabel}</small>
                    <small>{formatLabel(route.recipientIdentityStatus)} / {formatLabel(route.routeKind)}</small>
                  </span>
                  <span className="ledger-cell ledger-primary">
                    <span className={`asset-chip asset-${route.assetTone}`}>{route.assetDisplaySymbol}</span>
                    <small>{route.assetDescriptor}</small>
                  </span>
                  <span className="ledger-cell ledger-mono ledger-amount">{route.amountLabel}</span>
                </div>
              ))}
              {!routes.length ? (
                <div className="ledger-empty">
                  <strong>No matching routes.</strong>
                  <span>Broaden the window or clear filters to inspect the full treasury history.</span>
                </div>
              ) : null}
            </div>
          </div>
        </article>

        <div>
          <div className="section-head compact-head">
            <span className="eyebrow">Flow Map</span>
            <h2>Grouped by default for readability. Full topology only opens when the filter state is narrow enough.</h2>
          </div>
          <SankeyChart routes={routes} windowLabel={activeWindow?.label ?? "Treasury Window"} />
        </div>
      </section> : null}

      {showCategories ? <section className="section-block dense-three-up" id="signals">
        <article className="leaderboard-card treasury-ledger-card">
          <div className="section-head compact-head">
            <span className="eyebrow">Routing Shape</span>
            <h2>Cadence, route structure, and how much of the filtered view is project-linked.</h2>
          </div>
          <div className="stack-list compact">
            <article className="mini-row static">
              <span>Direct proposal to recipient routes</span>
              <strong>{formatNumber(directRouteCount)}</strong>
            </article>
            <article className="mini-row static">
              <span>Project-linked routes</span>
              <strong>{formatNumber(projectLinkedCount)}</strong>
            </article>
            <article className="mini-row static">
              <span>Recipients in current filter state</span>
              <strong>{formatNumber(routeSummary.recipientCount)}</strong>
            </article>
            <article className="mini-row static">
              <span>Proposals carrying routed value</span>
              <strong>{formatNumber(routeSummary.proposalCount)}</strong>
            </article>
          </div>
        </article>

        <article className="leaderboard-card treasury-ledger-card">
          <div className="section-head compact-head">
            <span className="eyebrow">Core Asset Concentration</span>
            <h2>The strongest treasury signal today is recipient concentration, especially in USDC and ETH.</h2>
          </div>
          <div className="stack-list compact">
            {coreConcentration.map((row) => (
              <article key={row.symbol} className="mini-row static">
                <span>
                  {formatAssetSymbol(row.symbol)} · Top 5 {row.top5_share_pct ?? "n/a"}% · Top 10 {row.top10_share_pct ?? "n/a"}%
                </span>
                <strong>{formatAmount(row.symbol, row.total_amount)}</strong>
              </article>
            ))}
          </div>
        </article>

        <article className="leaderboard-card treasury-ledger-card" id="categories">
          <div className="section-head compact-head">
            <span className="eyebrow">Category Allocation</span>
            <h2>How routed capital clusters across the current filter state.</h2>
          </div>
          <div className="ledger-table compact-ledger">
            <div className="ledger-head">
              <span>Category</span>
              <span>Routed</span>
              <span>Proposals</span>
              <span>Recipients</span>
            </div>
            <div className="ledger-body">
              {routeSummary.categoryRows.map((row) => (
                <div key={row.label} className="ledger-row">
                  <span className="ledger-cell ledger-primary">
                    <strong>{row.label}</strong>
                    <small>{row.routeCount} routes</small>
                  </span>
                  <span className="ledger-cell ledger-mono">
                    {row.totalsByAsset.map((item) => formatAmount(item.symbol, item.amount, item.tokenContract)).join(" + ")}
                  </span>
                  <span className="ledger-cell ledger-mono">{row.proposalCount.size}</span>
                  <span className="ledger-cell ledger-mono">{row.recipientCount.size}</span>
                </div>
              ))}
            </div>
          </div>
        </article>
      </section> : null}

      {showRecipients ? <section className="section-block dense-two-up" id="recipients">
        <article className="leaderboard-card treasury-ledger-card">
          <div className="section-head compact-head">
            <span className="eyebrow">Recipients</span>
            <h2>Who receives routed capital, with auditable identity and route density visible.</h2>
          </div>
          <div className="ledger-table compact-ledger">
            <div className="ledger-head">
              <span>Recipient</span>
              <span>Total</span>
              <span>Routes</span>
              <span>Projects</span>
            </div>
            <div className="ledger-body">
              {routeSummary.recipientRows.slice(0, 18).map((recipient) => (
                <div key={`${recipient.label}:${recipient.secondaryLabel}`} className="ledger-row">
                  <span className="ledger-cell ledger-primary">
                    {recipient.href ? <a href={recipient.href}>{recipient.label}</a> : <strong>{recipient.label}</strong>}
                    <small>{recipient.secondaryLabel}</small>
                    <small>{formatLabel(recipient.identityStatus)}</small>
                  </span>
                  <span className="ledger-cell ledger-mono">
                    {recipient.totalsByAsset.map((item) => formatAmount(item.symbol, item.amount, item.tokenContract)).join(" + ")}
                  </span>
                  <span className="ledger-cell ledger-mono">{recipient.routeCount}</span>
                  <span className="ledger-cell ledger-mono">{recipient.projectCount.size}</span>
                </div>
              ))}
            </div>
          </div>
        </article>

        <article className="leaderboard-card treasury-ledger-card">
          <div className="section-head compact-head">
            <span className="eyebrow">Top Recipients By Asset</span>
            <h2>Concentration is broken out by asset instead of forcing fake cross-token comparability.</h2>
          </div>
          <div className="stack-list compact">
            {coreConcentration.map((row) => (
              <article key={row.symbol} className="treasury-note-box compact">
                <strong>{formatAssetSymbol(row.symbol)}</strong>
                <span>
                  Top 5 = {row.top5_share_pct ?? "n/a"}% / Top 10 = {row.top10_share_pct ?? "n/a"}% / {row.top_recipients.length} named rows
                </span>
                <div className="stack-list compact">
                  {row.top_recipients.slice(0, 5).map((recipient) => (
                    <article key={`${row.symbol}:${recipient.slug}`} className="mini-row static">
                      <span>{recipient.display_name}</span>
                      <strong>{formatAmount(row.symbol, recipient.amount)}</strong>
                    </article>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </article>
      </section> : null}

      {showCategories ? <section className="section-block dense-two-up" id="assets">
        <article className="leaderboard-card">
          <div className="section-head compact-head">
            <span className="eyebrow">Current Holdings</span>
            <h2>Current treasury composition, valued in USD.</h2>
          </div>
          <AssetBars items={holdingsBars} emptyLabel="No assets" />
          <p className="treasury-note">
            Holdings are current treasury balances. Routed value below is proposal-linked outflow, not a treasury balance chart.
          </p>
        </article>
        <article className="leaderboard-card">
          <div className="section-head compact-head">
            <span className="eyebrow">Routing Windows</span>
            <h2>Short and long windows for treasury movement.</h2>
          </div>
          <div className="stack-list compact">
            {props.windows.map((window) => (
              <article key={window.window_id} className="mini-row static">
                <span>{window.totals_by_asset.map((item) => formatAmount(item.symbol, item.amount)).join(" + ") || "No routed value"}</span>
                <strong>
                  {window.label} / {window.route_count} routes / {window.recipient_count} recipients
                </strong>
              </article>
            ))}
          </div>
        </article>
      </section> : null}

      {showFlows ? <section className="section-block" id="proposals">
        <div className="section-head compact-head">
          <span className="eyebrow">Proposal Lineage</span>
          <h2>Requested versus routed capital, with zero-route proposals separated from actual treasury movement.</h2>
        </div>
        <div className="ledger-table">
          <div className="ledger-head">
            <span>Proposal</span>
            <span>Proposer</span>
            <span>Requested</span>
            <span>Routed</span>
            <span>Receipts</span>
          </div>
          <div className="ledger-body">
            {routedProposalRows.slice(0, 24).map((row) => (
              <div key={row.archiveId} className="ledger-row">
                <span className="ledger-cell ledger-primary">
                  <a href={row.href}>{row.numberLabel}</a>
                  <small>{row.title}</small>
                  <small>{row.status} / {row.category} / {row.proposalChain}</small>
                </span>
                <span className="ledger-cell ledger-primary">
                  {row.proposerHref ? <a href={row.proposerHref}>{row.proposerLabel}</a> : <strong>{row.proposerLabel}</strong>}
                  <small>{row.projectLabel ?? "No linked project"}</small>
                </span>
                <span className="ledger-cell ledger-mono">{row.requestedLabel}</span>
                <span className="ledger-cell ledger-mono">{row.routedLabel}</span>
                <span className="ledger-cell ledger-mono">
                  {row.routeCount} routes / {row.recipientCount} recipients / {row.proofCount} proofs
                </span>
              </div>
            ))}
          </div>
        </div>
        {zeroRouteRows.length ? (
          <div className="treasury-note-box">
            <strong>{zeroRouteRows.length} proposals in the current filter state have no decoded routed treasury value.</strong>
            <span>They remain governance records, but are intentionally separated from the treasury lineage ledger above.</span>
          </div>
        ) : null}
      </section> : null}

      {showReconciliation ? (
        <>
          <section className="section-block dense-three-up" id="reconciliation-summary">
            <article className="leaderboard-card treasury-ledger-card">
              <div className="section-head compact-head">
                <span className="eyebrow">Route Matching</span>
                <h2>{reconciliationSummary.matched_count} matched treasury routes.</h2>
              </div>
              <div className="stack-list compact">
                <article className="mini-row static">
                  <span>Visible matched routes</span>
                  <strong>{formatNumber(visibleTreasuryReconciliation.filter((row) => row.reconciliation_status === "matched").length)}</strong>
                </article>
                <article className="mini-row static">
                  <span>Visible needs review</span>
                  <strong>{formatNumber(visibleTreasuryReconciliation.filter((row) => row.reconciliation_status === "needs-review").length)}</strong>
                </article>
                <article className="mini-row static">
                  <span>Current window rows</span>
                  <strong>{formatNumber(visibleTreasuryReconciliation.length)}</strong>
                </article>
              </div>
            </article>

            <article className="leaderboard-card treasury-ledger-card">
              <div className="section-head compact-head">
                <span className="eyebrow">Proposal Matching</span>
                <h2>{props.proposalReconciliation.summary.matched_count} proposals reconcile cleanly.</h2>
              </div>
              <div className="stack-list compact">
                <article className="mini-row static">
                  <span>Visible proposal rows</span>
                  <strong>{formatNumber(visibleProposalReconciliation.length)}</strong>
                </article>
                <article className="mini-row static">
                  <span>Needs review</span>
                  <strong>{formatNumber(visibleProposalReconciliation.filter((row) => row.reconciliation_status === "needs-review").length)}</strong>
                </article>
                <article className="mini-row static">
                  <span>Site vs chain status diffs</span>
                  <strong>{formatNumber(visibleProposalReconciliation.filter((row) => row.site_status !== row.chain_status).length)}</strong>
                </article>
              </div>
            </article>

            <article className="leaderboard-card treasury-ledger-card">
              <div className="section-head compact-head">
                <span className="eyebrow">Contract Registry</span>
                <h2>Public contract language is anchored to the registry, then checked against chain visibility.</h2>
              </div>
              <div className="stack-list compact">
                <article className="mini-row static">
                  <span>Visible contract rows</span>
                  <strong>{formatNumber(visibleContractReconciliation.length)}</strong>
                </article>
                <article className="mini-row static">
                  <span>Matched contracts</span>
                  <strong>{formatNumber(visibleContractReconciliation.filter((row) => row.reconciliation_status === "matched").length)}</strong>
                </article>
                <article className="mini-row static">
                  <span>Chain-only contracts</span>
                  <strong>{formatNumber(visibleContractReconciliation.filter((row) => row.reconciliation_status === "chain-only").length)}</strong>
                </article>
              </div>
            </article>

            <article className="leaderboard-card treasury-ledger-card">
              <div className="section-head compact-head">
                <span className="eyebrow">Method</span>
                <h2>Resolved value uses chain truth for treasury, gnars.com for proposal language, and verified identity provenance for people.</h2>
              </div>
              <div className="stack-list compact">
                <article className="mini-row static">
                  <span>Source precedence</span>
                  <strong>Chain / Site / ENS / Override</strong>
                </article>
                <article className="mini-row static">
                  <span>Analytics build</span>
                  <strong>{asOfLabel}</strong>
                </article>
                <article className="mini-row static">
                  <span>Current window</span>
                  <strong>{activeWindow?.label ?? "All Time"}</strong>
                </article>
              </div>
            </article>
          </section>

          <section className="section-block dense-two-up" id="reconciliation-ledgers">
            <article className="leaderboard-card treasury-ledger-card">
              <div className="section-head compact-head">
                <span className="eyebrow">Treasury Route Reconciliation</span>
                <h2>Each decoded route is checked against proposal lineage, asset visibility, and the evidence surface.</h2>
              </div>
              <div className="ledger-table">
                <div className="ledger-head">
                  <span>Proposal</span>
                  <span>Recipient</span>
                  <span>Asset</span>
                  <span>Status</span>
                  <span>Evidence</span>
                </div>
                <div className="ledger-body">
                  {visibleTreasuryReconciliation.slice(0, 24).map((row) => (
                    <div key={row.route_id} className="ledger-row">
                      <span className="ledger-cell ledger-primary">
                        <a href={`/proposals/${row.archive_id}/`}>{row.proposal_number ? `Prop ${row.proposal_number}` : "Proposal"}</a>
                        <small>{row.proposal_title}</small>
                        <small>{formatLabel(row.chain)}</small>
                      </span>
                      <span className="ledger-cell ledger-primary">
                        <strong>{row.recipient_display_name}</strong>
                        <small>{row.recipient_address}</small>
                      </span>
                      <span className="ledger-cell ledger-primary">
                        <strong>{formatAmount(row.asset_symbol, row.amount, row.token_contract)}</strong>
                        <small>{formatLabel(row.asset_contract_status)}</small>
                      </span>
                      <span className="ledger-cell ledger-primary">
                        <span className={`tag ${reconciliationTone(row.reconciliation_status)}`}>{formatLabel(row.reconciliation_status)}</span>
                        <small>{row.mismatch_fields.join(", ") || "No mismatch fields"}</small>
                      </span>
                      <span className="ledger-cell ledger-primary">
                        <strong>{row.evidence_urls.length} sources</strong>
                        <small>{row.evidence_urls.length ? "Site / contract / lineage evidence" : "No evidence urls"}</small>
                      </span>
                    </div>
                  ))}
                  {!visibleTreasuryReconciliation.length ? (
                    <div className="ledger-empty">
                      <strong>No treasury reconciliation rows match the current filter state.</strong>
                      <span>Broaden search, chain, or window to inspect the full audit trail.</span>
                    </div>
                  ) : null}
                </div>
              </div>
            </article>

            <article className="leaderboard-card treasury-ledger-card">
              <div className="section-head compact-head">
                <span className="eyebrow">Proposal Reconciliation</span>
                <h2>Proposal language comes from gnars.com semantics, but the chain status stays visible beside it.</h2>
              </div>
              <div className="ledger-table">
                <div className="ledger-head">
                  <span>Proposal</span>
                  <span>Site</span>
                  <span>Chain</span>
                  <span>Resolved</span>
                  <span>Evidence</span>
                </div>
                <div className="ledger-body">
                  {visibleProposalReconciliation.slice(0, 18).map((row) => (
                    <div key={row.archive_id} className="ledger-row">
                      <span className="ledger-cell ledger-primary">
                        <a href={`/proposals/${row.archive_id}/`}>{row.proposal_number ? `Prop ${row.proposal_number}` : row.archive_id}</a>
                        <small>{row.title}</small>
                        <small>{formatLabel(row.platform)} / {formatLabel(row.chain)}</small>
                      </span>
                      <span className="ledger-cell ledger-primary">
                        <strong>{formatLabel(row.site_status)}</strong>
                      </span>
                      <span className="ledger-cell ledger-primary">
                        <strong>{formatLabel(row.chain_status)}</strong>
                      </span>
                      <span className="ledger-cell ledger-primary">
                        <span className={`tag ${reconciliationTone(row.reconciliation_status)}`}>{formatLabel(row.resolved_status)}</span>
                        <small>{formatLabel(row.reconciliation_status)}</small>
                      </span>
                      <span className="ledger-cell ledger-primary">
                        <strong>{row.evidence_urls.length} sources</strong>
                        <small>{row.mismatch_fields.join(", ") || "No mismatch fields"}</small>
                      </span>
                    </div>
                  ))}
                  {!visibleProposalReconciliation.length ? (
                    <div className="ledger-empty">
                      <strong>No proposal reconciliation rows match the current filter state.</strong>
                      <span>Clear filters to audit the full proposal registry.</span>
                    </div>
                  ) : null}
                </div>
              </div>
            </article>
          </section>

          <section className="section-block" id="contract-ledger">
            <div className="section-head compact-head">
              <span className="eyebrow">Contract Reconciliation</span>
              <h2>What powers Gnars onchain, and how much of that public surface is already anchored in the registry.</h2>
            </div>
            <div className="ledger-table compact-ledger">
              <div className="ledger-head">
                <span>Contract</span>
                <span>Network</span>
                <span>Status</span>
                <span>Evidence</span>
              </div>
              <div className="ledger-body">
                {visibleContractReconciliation.slice(0, 24).map((row) => (
                  <div key={row.contract_id} className="ledger-row">
                    <span className="ledger-cell ledger-primary">
                      <strong>{row.label}</strong>
                      <small>{row.kind}</small>
                      <small>{row.address}</small>
                    </span>
                    <span className="ledger-cell ledger-primary">
                      <strong>{formatLabel(row.network)}</strong>
                      <small>{formatLabel(row.ecosystem)}</small>
                    </span>
                    <span className="ledger-cell ledger-primary">
                      <span className={`tag ${reconciliationTone(row.reconciliation_status)}`}>{formatLabel(row.reconciliation_status)}</span>
                      <small>{formatLabel(row.status)}</small>
                    </span>
                    <span className="ledger-cell ledger-primary">
                      <strong>{row.evidence_urls.length} sources</strong>
                      <small>{row.evidence_urls.length ? "Registry / explorer / site evidence" : "No evidence urls"}</small>
                    </span>
                  </div>
                ))}
                {!visibleContractReconciliation.length ? (
                  <div className="ledger-empty">
                    <strong>No contract rows match the current filter state.</strong>
                    <span>Clear chain or search filters to inspect the full registry surface.</span>
                  </div>
                ) : null}
              </div>
            </div>
          </section>
        </>
      ) : null}
    </SiteLayout>
  );
}
