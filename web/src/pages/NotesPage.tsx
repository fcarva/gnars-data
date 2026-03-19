import { SiteLayout } from "../components/SiteLayout";
import type { Meta, NotesPageProps } from "../types";

export function NotesPage({ meta, props }: { meta: Meta; props: NotesPageProps }) {
  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Archive</span>
          <h1>Notes, docs, proposals, and operational writing.</h1>
          <p>The markdown vault remains public, but now sits inside the broader community and governance atlas.</p>
        </div>
      </section>
      <section className="dense-grid">
        {props.notes.map((note) => (
          <a key={note.slug} id={note.slug} className="feature-card" href={note.href}>
            <div className="tag-row">
              <span className="tag">{note.section}</span>
            </div>
            <h3>{note.title}</h3>
            <p>{note.excerpt}</p>
          </a>
        ))}
      </section>
    </SiteLayout>
  );
}
