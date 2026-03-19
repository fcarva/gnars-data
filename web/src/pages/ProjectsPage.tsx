import { useState } from "react";
import { SiteLayout } from "../components/SiteLayout";
import type { Meta, ProjectsPageProps } from "../types";

export function ProjectsPage({ meta, props }: { meta: Meta; props: ProjectsPageProps }) {
  const [activeFilter, setActiveFilter] = useState("All");
  const projects = props.projects.filter((project) => activeFilter === "All" || project.category === activeFilter);

  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Projects</span>
          <h1>Everything Gnars is shipping, funding, formalizing, or proving in public.</h1>
          <p>Projects are shown as delivery systems with proposal lineage, recipients, and proof of work.</p>
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
      <section className="masonry-grid dense">
        {projects.map((project) => (
          <a key={project.id} className="project-card" href={project.href}>
            <span className="project-status">{project.status}</span>
            <h3>{project.title}</h3>
            <p>{project.summary}</p>
            <div className="project-meta">
              <span>{project.category}</span>
              <span>{project.proposalTag}</span>
              <span>{project.budgetLabel}</span>
              <span>{project.updatedAt}</span>
            </div>
          </a>
        ))}
      </section>
    </SiteLayout>
  );
}
