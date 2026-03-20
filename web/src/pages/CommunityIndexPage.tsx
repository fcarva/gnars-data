import { useDeferredValue, useMemo } from "react";
import { FilterToolbar } from "../components/FilterToolbar";
import { NetworkMap } from "../components/NetworkMap";
import { SiteLayout } from "../components/SiteLayout";
import { filterCommunity } from "../lib/filtering";
import { useUrlState } from "../lib/urlState";
import type { CommunityIndexPageProps, Meta } from "../types";

export function CommunityIndexPage({ meta, props }: { meta: Meta; props: CommunityIndexPageProps }) {
  const [filters, setFilters] = useUrlState({
    tribe: "all",
    status: "all",
    search: "",
    sort: "date_desc",
  });
  const deferredSearch = useDeferredValue(filters.search);
  const people = useMemo(
    () => filterCommunity(props.people, { ...filters, search: deferredSearch }),
    [deferredSearch, filters, props.people],
  );

  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Community</span>
          <h1>People are readable as operators, athletes, delegates, recipients, and collaborators, not just wallets.</h1>
          <p>The directory is a public operating ledger: identity provenance, treasury lineage, proposal activity, and proof stay visible in one row.</p>
        </div>
      </section>

      <FilterToolbar
        searchValue={filters.search}
        searchPlaceholder="search people, tribes, roles"
        onSearchChange={(search) => setFilters({ search })}
        selectValue={filters.sort}
        selectOptions={[
          { value: "date_desc", label: "Recent activity" },
          { value: "usdc_received_desc", label: "USDC received" },
          { value: "eth_received_desc", label: "ETH received" },
          { value: "budget_managed_desc", label: "Budget managed" },
          { value: "proof_desc", label: "Proof count" },
        ]}
        onSelectChange={(sort) => setFilters({ sort })}
        groups={[
          {
            label: "Role",
            value: filters.tribe,
            options: props.facets.tribe,
            onChange: (tribe) => setFilters({ tribe }),
          },
          {
            label: "Status",
            value: filters.status,
            options: props.facets.status,
            onChange: (status) => setFilters({ status }),
          },
        ]}
      />

      <section className="section-block dense-two-up">
        <article className="leaderboard-card mini-map-panel">
          <div className="section-head compact-head">
            <span className="eyebrow">Map</span>
            <h2>Community remains connected to treasury, proposals, and projects.</h2>
          </div>
          <NetworkMap scene={props.economicMap} mode="full" />
        </article>
        <article className="leaderboard-card">
          <div className="section-head compact-head">
            <span className="eyebrow">Identity Read</span>
            <h2>{people.length} rows in the current filter state, ranked by activity and treasury context.</h2>
          </div>
          <div className="stack-list compact">
            <article className="mini-row static">
              <span>High confidence identities</span>
              <strong>{people.filter((person) => person.identityConfidence === "high").length}</strong>
            </article>
            <article className="mini-row static">
              <span>Recipient rows</span>
              <strong>{people.filter((person) => person.totalReceivedLabel !== "No successful treasury flows").length}</strong>
            </article>
            <article className="mini-row static">
              <span>Rows with proof</span>
              <strong>{people.filter((person) => person.proofCount > 0).length}</strong>
            </article>
          </div>
        </article>
      </section>

      <section className="section-block">
        <div className="ledger-table">
          <div className="ledger-head">
            <span>Identity</span>
            <span>Role / Provenance</span>
            <span>Received</span>
            <span>Managed</span>
            <span>Proof</span>
          </div>
          <div className="ledger-body">
            {people.slice(0, 72).map((person) => (
              <div key={person.slug} className="ledger-row">
                <span className="ledger-cell ledger-primary">
                  <a href={person.href}>{person.displayName}</a>
                  <small>{person.identityLabel}</small>
                  <small>{person.subtitle}</small>
                </span>
                <span className="ledger-cell ledger-primary">
                  <strong>{person.tribes.join(" / ")}</strong>
                  <small>{person.status}</small>
                  <small>{person.identitySource} / {person.identityConfidence}</small>
                </span>
                <span className="ledger-cell ledger-mono">{person.totalReceivedLabel}</span>
                <span className="ledger-cell ledger-mono">{person.budgetManagedLabel}</span>
                <span className="ledger-cell ledger-mono">{person.proofCount} proofs</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
