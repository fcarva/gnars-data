import type { ReactNode } from "react";
import type { Meta } from "../types";
import { SearchBox } from "./SearchBox";
import { ThemeToggle } from "./ThemeToggle";

const NAV_ITEMS: { href: string; label: string; key: Meta["activeNav"] }[] = [
  { href: "/", label: "Home", key: "home" },
  { href: "/community/", label: "Community", key: "community" },
  { href: "/network/", label: "Map", key: "network" },
  { href: "/treasury/", label: "Flows", key: "treasury" },
  { href: "/projects/", label: "Projects", key: "projects" },
  { href: "/proposals/", label: "Governance", key: "governance" },
  { href: "/timeline/", label: "Timeline", key: "timeline" },
  { href: "/notes/", label: "Archive", key: "archive" },
];

export function SiteLayout({
  meta,
  children,
}: {
  meta: Meta;
  children: ReactNode;
}) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <a className="brandmark" href="/">
          <span className="brandmark-badge">[]</span>
          <span>
            <strong>GNARS.CAMP</strong>
            <small>lab / field / governance / treasury / delivery</small>
          </span>
        </a>
        <nav className="top-nav" aria-label="Primary">
          {NAV_ITEMS.map((item) => (
            <a key={item.href} className={item.key === meta.activeNav ? "is-active" : ""} href={item.href}>
              {item.label}
            </a>
          ))}
        </nav>
        <div className="toolbar">
          <SearchBox />
          <ThemeToggle />
        </div>
      </header>
      <main className="app-main">{children}</main>
      <footer className="app-footer">
        <div>
          <strong>Gnars Camp v3</strong>
          <span>Static research atlas for the Gnars economic graph.</span>
        </div>
        <div>
          <a href="https://www.gnars.com/">gnars.com</a>
          <a href="https://www.gnars.center/">gnars.center</a>
          <a href="https://www.gnars.wtf/">gnars.wtf</a>
        </div>
      </footer>
    </div>
  );
}
