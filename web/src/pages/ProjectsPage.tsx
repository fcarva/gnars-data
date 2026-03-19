import { useDeferredValue, useMemo } from "react";
import { FilterToolbar } from "../components/FilterToolbar";
import { SiteLayout } from "../components/SiteLayout";
import { filterProjects } from "../lib/filtering";
import { useUrlState } from "../lib/urlState";
import type { Meta, ProjectsPageProps } from "../types";

export function ProjectsPage({ meta, props }: { meta: Meta; props: ProjectsPageProps }) {
  const [filters, setFilters] = useUrlState({
    category: "all",
    status: "all",
    search: "",
    sort: "date_desc",
  });
  const deferredSearch = useDeferredValue(filters.search);
  const projects = useMemo(
    () => filterProjects(props.projects, { ...filters, search: deferredSearch }),
    [deferredSearch, filters, props.projects],
  );

  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Projects</span>
          <h1>Workstreams, deliveries, and funded systems, organized as a registry instead of a portfolio wall.</h1>
          <p>Filter by category and status, then sort by recent movement, proof, or delivery volume.</p>
        </div>
      </section>

      <FilterToolbar
        searchValue={filters.search}
        searchPlaceholder="search projects, outputs, tags"
        onSearchChange={(search) => setFilters({ search })}
        selectValue={filters.sort}
        selectOptions={[
          { value: "date_desc", label: "Recent update" },
          { value: "proof_desc", label: "Proof count" },
          { value: "delivery_desc", label: "Delivery count" },
        ]}
        onSelectChange={(sort) => setFilters({ sort })}
        groups={[
          {
            label: "Category",
            value: filters.category,
            options: props.facets.category,
            onChange: (category) => setFilters({ category }),
          },
          {
            label: "Status",
            value: filters.status,
            options: props.facets.status,
            onChange: (status) => setFilters({ status }),
          },
        ]}
      />

      <section className="stack-list compact">
        {projects.map((project) => (
          <a key={project.id} className="directory-row" href={project.href}>
            <div className="directory-main">
              <div className="timeline-meta">
                <span>{project.category}</span>
                <span>{project.status}</span>
                <span>{project.proposalTag}</span>
              </div>
              <strong>{project.title}</strong>
              <p>{project.summary}</p>
            </div>
            <div className="directory-stats">
              <span>{project.budgetLabel}</span>
              <span>{project.spentLabel}</span>
              <span>{project.deliveryCount} deliveries</span>
            </div>
          </a>
        ))}
      </section>
    </SiteLayout>
  );
}
