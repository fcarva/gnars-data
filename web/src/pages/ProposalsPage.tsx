import { useDeferredValue, useMemo } from "react";
import { FilterToolbar } from "../components/FilterToolbar";
import { formatLabel } from "../lib/format";
import { SiteLayout } from "../components/SiteLayout";
import { filterProposals } from "../lib/filtering";
import { useUrlState } from "../lib/urlState";
import type { Meta, ProposalsPageProps } from "../types";

export function ProposalsPage({ meta, props }: { meta: Meta; props: ProposalsPageProps }) {
  const [filters, setFilters] = useUrlState({
    status: "all",
    category: "all",
    window: "all",
    search: "",
    sort: "date_desc",
  });
  const deferredSearch = useDeferredValue(filters.search);
  const proposals = useMemo(
    () => filterProposals(props.proposals, { ...filters, search: deferredSearch }),
    [deferredSearch, filters, props.proposals],
  );

  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Governance</span>
          <h1>Governance is legible as a ledger of capital, labor, category, and public direction.</h1>
          <p>Dense rows replace card walls: status, category, budget, votes, and proposal lineage stay visible together.</p>
        </div>
      </section>

      <FilterToolbar
        searchValue={filters.search}
        searchPlaceholder="search titles, proposers, categories"
        onSearchChange={(search) => setFilters({ search })}
        selectValue={filters.sort}
        selectOptions={[
          { value: "date_desc", label: "Recent first" },
          { value: "budget_desc", label: "Budget routed" },
          { value: "votes_desc", label: "Vote count" },
        ]}
        onSelectChange={(sort) => setFilters({ sort })}
        groups={[
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
            label: "Window",
            value: filters.window,
            options: [
              { value: "30d", label: "30d", count: 0 },
              { value: "6m", label: "6m", count: 0 },
              { value: "all", label: "All Time", count: 0 },
            ],
            onChange: (window) => setFilters({ window }),
          },
        ]}
      />

      <section className="section-block">
        <div className="section-head compact-head">
          <span className="eyebrow">{props.signals.label}</span>
          <h2>
            {props.signals.metrics.payout_count} treasury routes, {props.signals.metrics.proposal_count} proposals,{" "}
            {props.signals.metrics.delivery_count} delivery signals.
          </h2>
        </div>
      </section>

      <section className="stack-list compact">
        {proposals.map((proposal) => (
          <a key={proposal.archiveId} className="directory-row" href={proposal.href}>
            <div className="directory-main">
              <div className="timeline-meta">
                <span>{proposal.numberLabel}</span>
                <span>{formatLabel(proposal.status)}</span>
                <span>{formatLabel(proposal.category)}</span>
                {proposal.hot ? <span>Hot</span> : null}
              </div>
              <strong>{proposal.title}</strong>
              <p>{proposal.summary}</p>
            </div>
            <div className="directory-stats">
              <span>{proposal.proposerLabel}</span>
              <span>{proposal.budgetLabel}</span>
              <span>{proposal.voteCount} votes</span>
            </div>
          </a>
        ))}
      </section>
    </SiteLayout>
  );
}
