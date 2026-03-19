import { SiteLayout } from "../components/SiteLayout";
import { TimelineFeed } from "../components/TimelineFeed";
import type { Meta, TimelinePageProps } from "../types";

export function TimelinePage({ meta, props }: { meta: Meta; props: TimelinePageProps }) {
  return (
    <SiteLayout meta={meta}>
      <section className="hero-panel compact">
        <div>
          <span className="eyebrow">Timeline</span>
          <h1>The running chronology of what Gnars proposed, funded, and delivered.</h1>
          <p>Timeline events merge proposal outcomes, workstream updates, and public proof links into one surface.</p>
        </div>
      </section>
      <TimelineFeed items={props.timeline} />
    </SiteLayout>
  );
}
