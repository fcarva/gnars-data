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
          <p>The directory is dense on purpose: labels, receipts, proposal history, and proof all stay visible.</p>
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
            label: "Tribe",
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
        <div className="stack-list compact">
          {people.slice(0, 36).map((person) => (
            <a key={person.slug} className="directory-row" href={person.href}>
              <div className="directory-main">
                <div className="timeline-meta">
                  <span>{person.tribes.join(" / ")}</span>
                  <span>{person.status}</span>
                </div>
                <strong>{person.displayName}</strong>
                <p>{person.subtitle}</p>
              </div>
              <div className="directory-stats">
                <span>{person.totalReceivedLabel}</span>
                <span>{person.budgetManagedLabel}</span>
                <span>{person.proofCount} proofs</span>
              </div>
            </a>
          ))}
        </div>
      </section>
    </SiteLayout>
  );
}
