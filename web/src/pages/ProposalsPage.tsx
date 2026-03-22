import { useDeferredValue, useMemo } from "react";
import { FilterToolbar } from "../components/FilterToolbar";
import { formatLabel } from "../lib/format";
import { SiteLayout } from "../components/SiteLayout";
import { filterProposals } from "../lib/filtering";
import { useUrlState } from "../lib/urlState";
import type { Meta, ProposalsPageProps } from "../types";

function inWindow(date: string, days: number) {
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) {
    return false;
  }
  return parsed.getTime() >= Date.now() - days * 24 * 60 * 60 * 1000;
}

function truncateTitle(value: string | null | undefined, maxLength = 88) {
  if (!value) {
    return "Untitled proposal";
  }
  const clean = value
    .replace(/^#+\s+/gm, "")
    .replace(/\n[\s\S]*/, "")
    .trim();
  if (clean.length <= maxLength) {
    return clean;
  }
  return `${clean.slice(0, maxLength - 1).trimEnd()}...`;
}

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
  const windowOptions = useMemo(
    () => [
      { value: "30d", label: "30d", count: props.proposals.filter((proposal) => inWindow(proposal.date, 30)).length },
      { value: "6m", label: "6m", count: props.proposals.filter((proposal) => inWindow(proposal.date, 183)).length },
    ],
    [props.proposals],
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
            options: windowOptions,
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

      <section className="section-block">
        <div className="ledger-table">
          <div className="ledger-head">
            <span>Proposal</span>
            <span>Status / Chain</span>
            <span>Requested</span>
            <span>Routed</span>
            <span>Votes</span>
          </div>
          <div className="ledger-body">
            {proposals.map((proposal) => (
              <div key={proposal.archiveId} className="ledger-row">
                <span className="ledger-cell ledger-primary">
                  <strong>
                    <a href={proposal.href}>{proposal.numberLabel}</a>
                  </strong>
                  <span>{truncateTitle(proposal.title)}</span>
                  <small>{proposal.summary}</small>
                  <small>{proposal.proposerLabel} / {proposal.proposerSecondaryLabel}</small>
                </span>
                <span className="ledger-cell ledger-primary">
                  <strong>{formatLabel(proposal.resolvedStatus || proposal.status)}</strong>
                  <small>{formatLabel(proposal.chain)}</small>
                  <small>{formatLabel(proposal.category)} {proposal.hot ? "/ Hot" : ""}</small>
                  <small>{proposal.reconciliationStatus === "needs-review" ? "Needs review" : "Matched"}</small>
                </span>
                <span className="ledger-cell ledger-mono">{proposal.requestedLabel}</span>
                <span className="ledger-cell ledger-mono">{proposal.routedLabel}</span>
                <span className="ledger-cell ledger-mono">
                  {proposal.voteCount} votes
                  <small>{proposal.quorumLabel}</small>
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
