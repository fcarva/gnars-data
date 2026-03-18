from __future__ import annotations

import csv
import html
import json
import posixpath
import re
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "_site"
DATA_DIR = ROOT / "data"
EXPORTS_DIR = ROOT / "exports"
MEDIA_DIR = ROOT / "media"


SITE_CSS = """
:root {
  --bg: #f7f1e4;
  --surface: rgba(255, 251, 242, 0.9);
  --surface-strong: #fffaf0;
  --text: #171311;
  --muted: #65554b;
  --line: rgba(23, 19, 17, 0.12);
  --accent: #f18f01;
  --accent-dark: #ca6f00;
  --pill: #fce945;
  --shadow: 0 18px 40px rgba(23, 19, 17, 0.08);
  --max: 1200px;
}

* {
  box-sizing: border-box;
}

html {
  color-scheme: light;
}

body {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  color: var(--text);
  background:
    radial-gradient(circle at top left, rgba(252, 233, 69, 0.45), transparent 28%),
    radial-gradient(circle at top right, rgba(241, 143, 1, 0.16), transparent 24%),
    linear-gradient(180deg, #fdf8ee 0%, var(--bg) 100%);
  min-height: 100vh;
}

a {
  color: inherit;
}

.shell {
  width: min(calc(100% - 32px), var(--max));
  margin: 0 auto;
  padding: 24px 0 48px;
}

.hero,
.panel,
.note,
.dataset-card,
.stat {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 20px;
  box-shadow: var(--shadow);
}

.hero {
  padding: 28px;
  margin-bottom: 24px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--pill);
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.hero h1,
.note h1 {
  margin: 14px 0 10px;
  font-size: clamp(2.2rem, 5vw, 4.5rem);
  line-height: 0.95;
}

.hero p,
.lede,
.meta,
.note p,
.note li,
.dataset-card p,
table,
code,
pre {
  font-size: 1rem;
  line-height: 1.7;
}

.muted,
.meta,
.note .meta {
  color: var(--muted);
}

.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 20px 0 0;
}

.nav a,
.button,
.tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 999px;
  text-decoration: none;
  border: 1px solid var(--line);
  background: var(--surface-strong);
}

.button {
  background: var(--accent);
  color: #fff;
  border-color: transparent;
  font-weight: 700;
}

.button.secondary {
  background: var(--surface-strong);
  color: var(--text);
  border-color: var(--line);
}

.grid {
  display: grid;
  gap: 18px;
}

.grid.stats {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-bottom: 24px;
}

.grid.cards,
.grid.datasets {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.stat,
.panel,
.dataset-card,
.note {
  padding: 22px;
}

.stat strong {
  display: block;
  font-size: 2rem;
  margin-bottom: 8px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  margin: 0 0 16px;
}

.section-head h2 {
  margin: 0;
  font-size: 1.35rem;
}

.stack {
  display: grid;
  gap: 16px;
}

.note-layout {
  display: grid;
  grid-template-columns: minmax(0, 250px) minmax(0, 1fr);
  gap: 24px;
}

.sidebar {
  position: sticky;
  top: 24px;
  align-self: start;
}

.sidebar ul {
  list-style: none;
  padding: 0;
  margin: 16px 0 0;
  display: grid;
  gap: 8px;
}

.sidebar a {
  text-decoration: none;
}

.note h1,
.note h2,
.note h3,
.note h4,
.note h5,
.note h6 {
  line-height: 1.15;
  margin: 1.2em 0 0.5em;
}

.note h2 {
  font-size: 1.6rem;
}

.note h3 {
  font-size: 1.25rem;
}

.note p,
.note ul,
.note ol,
.note pre,
.note table,
.note blockquote {
  margin: 0 0 1rem;
}

.note ul,
.note ol {
  padding-left: 1.25rem;
}

.note blockquote {
  padding: 12px 16px;
  border-left: 4px solid var(--accent);
  background: rgba(241, 143, 1, 0.08);
  border-radius: 12px;
}

pre,
code {
  font-family: "Courier New", monospace;
}

pre {
  overflow-x: auto;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: #1a1714;
  color: #f7f1e4;
}

code {
  padding: 0.15em 0.4em;
  border-radius: 6px;
  background: rgba(23, 19, 17, 0.08);
}

pre code {
  padding: 0;
  background: transparent;
}

table {
  width: 100%;
  border-collapse: collapse;
  overflow-x: auto;
  display: block;
}

thead th {
  text-align: left;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

th,
td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}

.links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.path {
  font-family: "Courier New", monospace;
  font-size: 0.9rem;
}

.footer {
  margin-top: 28px;
  color: var(--muted);
  font-size: 0.95rem;
}

@media (max-width: 900px) {
  .note-layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
  }
}
"""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def site_relative(path: Path) -> str:
    return path.relative_to(SITE_DIR).as_posix()


def rel_href(from_page: Path, to_page: Path) -> str:
    return posixpath.relpath(site_relative(to_page), start=site_relative(from_page.parent))


def html_document(path: Path, *, title: str, body: str, description: str = "") -> str:
    css_href = rel_href(path, SITE_DIR / "assets" / "site.css")
    home_href = rel_href(path, SITE_DIR / "index.html")
    notes_href = rel_href(path, SITE_DIR / "notes" / "index.html")
    datasets_href = rel_href(path, SITE_DIR / "datasets" / "index.html")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}" />
  <link rel="stylesheet" href="{css_href}" />
</head>
<body>
  <div class="shell">
    <div class="nav">
      <a href="{home_href}">Home</a>
      <a href="{notes_href}">Notes</a>
      <a href="{datasets_href}">Datasets</a>
    </div>
    {body}
    <div class="footer">Built from the tracked repository state in <span class="path">gnars-data</span>.</div>
  </div>
</body>
</html>
"""


def load_json(name: str) -> Any:
    with (DATA_DIR / f"{name}.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def truncate(value: str, limit: int = 160) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def render_inline(text: str) -> str:
    code_tokens: list[str] = []

    def store_code(match: re.Match[str]) -> str:
        code_tokens.append(f"<code>{html.escape(match.group(1), quote=False)}</code>")
        return f"@@CODE{len(code_tokens) - 1}@@"

    text = re.sub(r"`([^`]+)`", store_code, text)
    text = html.escape(text, quote=False)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: f'<a href="{html.escape(match.group(2), quote=True)}">{match.group(1)}</a>',
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    for index, token in enumerate(code_tokens):
        text = text.replace(f"@@CODE{index}@@", token)
    return text


def render_markdown(markdown_text: str) -> str:
    lines = markdown_text.replace("\r\n", "\n").split("\n")
    parts: list[str] = []
    paragraph: list[str] = []
    in_code = False
    code_language = ""
    code_lines: list[str] = []
    i = 0

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            parts.append(f"<p>{render_inline(' '.join(paragraph))}</p>")
            paragraph = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if in_code:
            if stripped.startswith("```"):
                language_class = f' class="language-{html.escape(code_language, quote=True)}"' if code_language else ""
                parts.append(f"<pre><code{language_class}>{html.escape(chr(10).join(code_lines))}</code></pre>")
                in_code = False
                code_language = ""
                code_lines = []
            else:
                code_lines.append(line)
            i += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            in_code = True
            code_language = stripped[3:].strip()
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            flush_paragraph()
            level = len(heading_match.group(1))
            title = render_inline(heading_match.group(2).strip())
            anchor = re.sub(r"[^a-z0-9]+", "-", heading_match.group(2).lower()).strip("-") or "section"
            parts.append(f'<h{level} id="{anchor}">{title}</h{level}>')
            i += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            parts.append(f"<blockquote>{render_markdown(chr(10).join(quote_lines))}</blockquote>")
            continue

        unordered_match = re.match(r"^- (.*)$", stripped)
        ordered_match = re.match(r"^\d+\. (.*)$", stripped)
        if unordered_match or ordered_match:
            flush_paragraph()
            is_ordered = ordered_match is not None
            items = []
            while i < len(lines):
                current = lines[i].strip()
                current_match = re.match(r"^\d+\. (.*)$", current) if is_ordered else re.match(r"^- (.*)$", current)
                if not current_match:
                    break
                items.append(f"<li>{render_inline(current_match.group(1))}</li>")
                i += 1
            tag = "ol" if is_ordered else "ul"
            parts.append(f"<{tag}>{''.join(items)}</{tag}>")
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    return "\n".join(parts)


def note_title(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def note_summary(markdown_text: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("```"):
            return truncate(stripped, limit=180)
    return "Repository note."


def note_output_path(source: Path) -> Path:
    relative = source.relative_to(ROOT)
    if relative.as_posix() == "README.md":
        return SITE_DIR / "notes" / "home" / "index.html"
    return SITE_DIR / "notes" / relative.with_suffix("") / "index.html"


def discover_notes() -> list[dict[str, Any]]:
    note_paths = [
        ROOT / "README.md",
        ROOT / "data" / "README.md",
        ROOT / "exports" / "README.md",
        ROOT / "scripts" / "README.md",
        *sorted((ROOT / "docs").rglob("*.md")),
        *sorted((ROOT / "reports").rglob("*.md")),
    ]

    notes = []
    for path in note_paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        title = note_title(text, path.stem.replace("-", " ").title())
        notes.append(
            {
                "source": path,
                "relative_source": path.relative_to(ROOT).as_posix(),
                "title": title,
                "summary": note_summary(text),
                "html": render_markdown(text),
                "output": note_output_path(path),
            }
        )
    return notes


def preview_cell(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return truncate(json.dumps(value, ensure_ascii=False), limit=120)
    return truncate(str(value), limit=120)


def render_table(headers: list[str], rows: list[dict[str, Any]]) -> str:
    if not headers or not rows:
        return "<p class=\"muted\">No preview rows available.</p>"
    head_html = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{html.escape(preview_cell(row.get(header)))}</td>" for header in headers)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head_html}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def csv_preview(path: Path, *, limit: int = 8) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for index, row in enumerate(reader):
            if index >= limit:
                break
            rows.append(row)
        return reader.fieldnames or [], rows


def json_preview(path: Path, *, limit: int = 6) -> tuple[list[str], list[dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    metadata = {}
    if isinstance(payload, dict):
        metadata = {key: value for key, value in payload.items() if key != "records"}
        records = payload.get("records", [])
        if isinstance(records, list) and records:
            headers = list(records[0].keys())[:8]
            rows = [{key: row.get(key) for key in headers} for row in records[:limit]]
            return headers, rows, metadata
    return [], [], metadata


def dataset_page_path(kind: str, path: Path) -> Path:
    return SITE_DIR / "datasets" / kind / path.stem / "index.html"


def build_home(notes: list[dict[str, Any]]) -> None:
    archive = load_json("proposals_archive")
    treasury = load_json("treasury")
    members = load_json("members")
    contracts = load_json("contracts")
    proposal_tags = load_json("proposal_tags")

    proposal_count = len(archive["records"])
    vote_count = sum(len(record["votes"]) for record in archive["records"])
    tx_count = sum(len(record["transactions"]) for record in archive["records"])
    pilot_count = len(proposal_tags["records"])

    latest_rows = archive["records"][:5]
    latest_headers = ["archive_id", "platform", "proposal_number", "title", "status"]
    latest_table = render_table(latest_headers, latest_rows)

    latest_note_cards = []
    for note in notes[:6]:
        href = rel_href(SITE_DIR / "index.html", note["output"])
        latest_note_cards.append(
            f"""
            <div class="dataset-card">
              <div class="eyebrow">Note</div>
              <h3>{html.escape(note['title'])}</h3>
              <p class="muted">{html.escape(note['summary'])}</p>
              <div class="links"><a href="{href}">Open note</a></div>
            </div>
            """
        )

    exports_panel = []
    for path in sorted(EXPORTS_DIR.glob("*.csv"))[:6]:
        href = rel_href(SITE_DIR / "index.html", SITE_DIR / "exports" / path.name)
        preview_href = rel_href(SITE_DIR / "index.html", dataset_page_path("exports", path))
        exports_panel.append(
            f"""
            <div class="dataset-card">
              <div class="eyebrow">Export</div>
              <h3>{html.escape(path.name)}</h3>
              <p class="muted">Flat file for downloads, spreadsheets, BI, and automation.</p>
              <div class="links">
                <a href="{href}">Download</a>
                <a href="{preview_href}">Preview</a>
              </div>
            </div>
            """
        )

    body = f"""
    <div class="hero">
      <div class="eyebrow">Quartz-style Vault</div>
      <h1>Gnars DAO data, notes, and exports in one public base.</h1>
      <p class="lede">This GitHub Pages build turns the repository into a public Obsidian-style vault with direct CSV downloads, JSON datasets, operational notes, and proposal intelligence.</p>
      <div class="links">
        <a class="button" href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'exports' / 'proposals.csv')}">Download `proposals.csv`</a>
        <a class="button secondary" href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'notes' / 'index.html')}">Browse notes</a>
        <a class="button secondary" href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'datasets' / 'index.html')}">Browse datasets</a>
      </div>
    </div>

    <div class="grid stats">
      <div class="stat"><strong>{proposal_count}</strong><span class="muted">proposal records indexed</span></div>
      <div class="stat"><strong>{vote_count}</strong><span class="muted">votes archived</span></div>
      <div class="stat"><strong>{tx_count}</strong><span class="muted">decoded governance transactions</span></div>
      <div class="stat"><strong>{len(members['records'])}</strong><span class="muted">member records seeded</span></div>
      <div class="stat"><strong>{len(contracts['records'])}</strong><span class="muted">verified contracts</span></div>
      <div class="stat"><strong>{pilot_count}</strong><span class="muted">proposal-tag pilot queue</span></div>
      <div class="stat"><strong>{len(treasury['records'])}</strong><span class="muted">treasury assets tracked</span></div>
      <div class="stat"><strong>${treasury['overview']['treasury_page_total_value_usd']:.0f}</strong><span class="muted">treasury metric payload</span></div>
    </div>

    <div class="grid" style="grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr);">
      <div class="panel">
        <div class="section-head">
          <h2>Latest proposals</h2>
          <span class="meta">From `data/proposals_archive.json`</span>
        </div>
        {latest_table}
      </div>
      <div class="panel">
        <div class="section-head">
          <h2>Publishing</h2>
          <span class="meta">Direct file URLs</span>
        </div>
        <div class="stack">
          <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'exports' / 'proposals.csv')}">/exports/proposals.csv</a></div>
          <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'exports' / 'proposals_archive.csv')}">/exports/proposals_archive.csv</a></div>
          <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'data' / 'proposals_archive.json')}">/data/proposals_archive.json</a></div>
          <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'data' / 'proposal_tags.json')}">/data/proposal_tags.json</a></div>
        </div>
      </div>
    </div>

    <div class="panel" style="margin-top: 24px;">
      <div class="section-head">
        <h2>Recent notes</h2>
        <span class="meta">Governance, operations, publishing, tagging</span>
      </div>
      <div class="grid cards">
        {''.join(latest_note_cards)}
      </div>
    </div>

    <div class="panel" style="margin-top: 24px;">
      <div class="section-head">
        <h2>Downloads</h2>
        <span class="meta">CSV and JSON ready for anyone to fetch</span>
      </div>
      <div class="grid datasets">
        {''.join(exports_panel)}
      </div>
    </div>
    """
    page = html_document(SITE_DIR / "index.html", title="Gnars Data Vault", body=body, description="Public Gnars DAO data vault.")
    write_text(SITE_DIR / "index.html", page)


def build_notes_index(notes: list[dict[str, Any]]) -> None:
    cards = []
    for note in notes:
        href = rel_href(SITE_DIR / "notes" / "index.html", note["output"])
        cards.append(
            f"""
            <div class="dataset-card">
              <div class="eyebrow">{html.escape(note['relative_source'].split('/')[0])}</div>
              <h3>{html.escape(note['title'])}</h3>
              <p class="muted">{html.escape(note['summary'])}</p>
              <div class="meta path">{html.escape(note['relative_source'])}</div>
              <div class="links"><a href="{href}">Open note</a></div>
            </div>
            """
        )

    body = f"""
    <div class="hero">
      <div class="eyebrow">Notes</div>
      <h1>Repository knowledge base</h1>
      <p class="lede">Human-readable governance, operations, architecture, and archival context rendered from tracked markdown files.</p>
    </div>
    <div class="grid cards">
      {''.join(cards)}
    </div>
    """
    page = html_document(
        SITE_DIR / "notes" / "index.html",
        title="Gnars Notes",
        body=body,
        description="Rendered notes from the gnars-data repository.",
    )
    write_text(SITE_DIR / "notes" / "index.html", page)


def build_note_pages(notes: list[dict[str, Any]]) -> None:
    index_items = []
    for note in notes:
        note_href = rel_href(note["output"], note["output"])
        index_items.append(f'<li><a href="{note_href}">{html.escape(note["title"])}</a></li>')

    for note in notes:
        list_items = []
        for item in notes:
            href = rel_href(note["output"], item["output"])
            list_items.append(f'<li><a href="{href}">{html.escape(item["title"])}</a></li>')
        body = f"""
        <div class="hero">
          <div class="eyebrow">Note</div>
          <h1>{html.escape(note['title'])}</h1>
          <p class="lede">{html.escape(note['summary'])}</p>
          <div class="meta path">{html.escape(note['relative_source'])}</div>
        </div>
        <div class="note-layout">
          <aside class="panel sidebar">
            <div class="section-head"><h2>Vault</h2></div>
            <ul>{''.join(list_items)}</ul>
          </aside>
          <article class="note">
            {note['html']}
          </article>
        </div>
        """
        page = html_document(note["output"], title=note["title"], body=body, description=note["summary"])
        write_text(note["output"], page)


def build_dataset_pages() -> None:
    cards = []

    for path in sorted(DATA_DIR.glob("*.json")):
        headers, rows, metadata = json_preview(path)
        output = dataset_page_path("data", path)
        download_href = rel_href(output, SITE_DIR / "data" / path.name)
        preview_table = render_table(headers, rows)
        metadata_rows = "".join(
            f"<div><strong>{html.escape(key)}</strong>: {html.escape(preview_cell(value))}</div>"
            for key, value in metadata.items()
        ) or "<p class=\"muted\">No top-level metadata available.</p>"
        body = f"""
        <div class="hero">
          <div class="eyebrow">Dataset</div>
          <h1>{html.escape(path.name)}</h1>
          <p class="lede">Canonical JSON dataset published from the tracked repository state.</p>
          <div class="links"><a class="button" href="{download_href}">Download JSON</a></div>
        </div>
        <div class="panel">
          <div class="section-head"><h2>Metadata</h2></div>
          <div class="stack">{metadata_rows}</div>
        </div>
        <div class="panel" style="margin-top: 24px;">
          <div class="section-head"><h2>Preview</h2></div>
          {preview_table}
        </div>
        """
        page = html_document(output, title=path.name, body=body, description=f"Preview for {path.name}")
        write_text(output, page)

        cards.append(
            f"""
            <div class="dataset-card">
              <div class="eyebrow">JSON</div>
              <h3>{html.escape(path.name)}</h3>
              <p class="muted">Canonical structured dataset under `/data/`.</p>
              <div class="links">
                <a href="{rel_href(SITE_DIR / 'datasets' / 'index.html', output)}">Preview</a>
                <a href="{rel_href(SITE_DIR / 'datasets' / 'index.html', SITE_DIR / 'data' / path.name)}">Download</a>
              </div>
            </div>
            """
        )

    for path in sorted(EXPORTS_DIR.glob("*.csv")):
        headers, rows = csv_preview(path)
        output = dataset_page_path("exports", path)
        download_href = rel_href(output, SITE_DIR / "exports" / path.name)
        preview_table = render_table(headers[:10], rows)
        body = f"""
        <div class="hero">
          <div class="eyebrow">Export</div>
          <h1>{html.escape(path.name)}</h1>
          <p class="lede">Flat CSV export ready for spreadsheets, dashboards, and bulk downloads.</p>
          <div class="links"><a class="button" href="{download_href}">Download CSV</a></div>
        </div>
        <div class="panel">
          <div class="section-head"><h2>Preview</h2></div>
          {preview_table}
        </div>
        """
        page = html_document(output, title=path.name, body=body, description=f"Preview for {path.name}")
        write_text(output, page)

        cards.append(
            f"""
            <div class="dataset-card">
              <div class="eyebrow">CSV</div>
              <h3>{html.escape(path.name)}</h3>
              <p class="muted">Downloadable export under `/exports/`.</p>
              <div class="links">
                <a href="{rel_href(SITE_DIR / 'datasets' / 'index.html', output)}">Preview</a>
                <a href="{rel_href(SITE_DIR / 'datasets' / 'index.html', SITE_DIR / 'exports' / path.name)}">Download</a>
              </div>
            </div>
            """
        )

    body = f"""
    <div class="hero">
      <div class="eyebrow">Datasets</div>
      <h1>JSON and CSV publication layer</h1>
      <p class="lede">Browsable previews plus direct file URLs for machine downloads.</p>
    </div>
    <div class="grid datasets">
      {''.join(cards)}
    </div>
    """
    page = html_document(
        SITE_DIR / "datasets" / "index.html",
        title="Gnars Datasets",
        body=body,
        description="Published Gnars datasets and exports.",
    )
    write_text(SITE_DIR / "datasets" / "index.html", page)


def copy_public_directories() -> None:
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copytree(DATA_DIR, SITE_DIR / "data", dirs_exist_ok=True)
    shutil.copytree(EXPORTS_DIR, SITE_DIR / "exports", dirs_exist_ok=True)
    if MEDIA_DIR.exists():
        shutil.copytree(MEDIA_DIR, SITE_DIR / "media", dirs_exist_ok=True)

    write_text(SITE_DIR / ".nojekyll", "")
    write_text(SITE_DIR / "assets" / "site.css", SITE_CSS.strip() + "\n")


def main() -> int:
    copy_public_directories()
    notes = discover_notes()
    build_home(notes)
    build_notes_index(notes)
    build_note_pages(notes)
    build_dataset_pages()
    print(f"[ok] built {SITE_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
