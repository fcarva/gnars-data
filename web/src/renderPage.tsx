import type { PagePayload } from "./types";
import { HomePage } from "./pages/HomePage";
import { CommunityIndexPage } from "./pages/CommunityIndexPage";
import { CommunityProfilePage } from "./pages/CommunityProfilePage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { ProjectDetailPage } from "./pages/ProjectDetailPage";
import { ProposalsPage } from "./pages/ProposalsPage";
import { ProposalDetailPage } from "./pages/ProposalDetailPage";
import { TimelinePage } from "./pages/TimelinePage";
import { NetworkPage } from "./pages/NetworkPage";
import { TreasuryPage } from "./pages/TreasuryPage";
import { NotesPage } from "./pages/NotesPage";

export function renderPage(payload: PagePayload) {
  switch (payload.pageType) {
    case "home":
      return <HomePage meta={payload.meta} props={payload.props} />;
    case "community-index":
      return <CommunityIndexPage meta={payload.meta} props={payload.props} />;
    case "community-profile":
      return <CommunityProfilePage meta={payload.meta} props={payload.props} />;
    case "projects-index":
      return <ProjectsPage meta={payload.meta} props={payload.props} />;
    case "project-detail":
      return <ProjectDetailPage meta={payload.meta} props={payload.props} />;
    case "proposals-index":
      return <ProposalsPage meta={payload.meta} props={payload.props} />;
    case "proposal-detail":
      return <ProposalDetailPage meta={payload.meta} props={payload.props} />;
    case "timeline-index":
      return <TimelinePage meta={payload.meta} props={payload.props} />;
    case "network-index":
      return <NetworkPage meta={payload.meta} props={payload.props} />;
    case "treasury-index":
      return <TreasuryPage meta={payload.meta} props={payload.props} />;
    case "notes-index":
      return <NotesPage meta={payload.meta} props={payload.props} />;
    default:
      return null;
  }
}
