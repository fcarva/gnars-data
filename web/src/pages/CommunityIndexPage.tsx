import { useState } from "react";
import { SiteLayout } from "../components/SiteLayout";
import type { CommunityIndexPageProps, Meta } from "../types";

export function CommunityIndexPage({ meta, props }: { meta: Meta; props: CommunityIndexPageProps }) {
  const [activeFilter, setActiveFilter] = useState("All");
  const people = props.people.filter((person) => {
    if (activeFilter === "All") {
      return true;
    }
    return person.tribes.includes(activeFilter);
  });

  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Community</span>
          <h1>One directory for athletes, builders, filmmakers, organizers, delegates, and recipients.</h1>
          <p>This is the social and economic graph of Gnars, rendered as a browsable public dossier.</p>
        </div>
      </section>
      <div className="filter-row">
        {props.filters.map((filter) => (
          <button
            key={filter}
            className={filter === activeFilter ? "filter-pill is-active" : "filter-pill"}
            type="button"
            onClick={() => setActiveFilter(filter)}
          >
            {filter}
          </button>
        ))}
      </div>
      <section className="dense-grid">
        {people.map((person) => (
          <a key={person.slug} className="feature-card" href={person.href}>
            <div className="tag-row">
              {person.tribes.map((tribe) => (
                <span key={tribe} className="tag">
                  {tribe}
                </span>
              ))}
            </div>
            <h3>{person.displayName}</h3>
            <p>{person.subtitle}</p>
            <div className="feature-stats">
              <span>{person.totalReceivedLabel}</span>
              <span>{person.approvedProposals} passed</span>
              <span>{person.budgetManagedLabel}</span>
            </div>
          </a>
        ))}
      </section>
    </SiteLayout>
  );
}
