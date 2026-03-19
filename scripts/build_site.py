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
MEDIA_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif"}
MEDIA_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}


SITE_CSS = """
:root {
  --bg: #fffcf0;
  --bg-soft: #f2f0e5;
  --surface: rgba(255, 252, 240, 0.96);
  --surface-strong: #f2f0e5;
  --surface-hover: #ede9dc;
  --text: #100f0f;
  --muted: #6f6e69;
  --line: #dad8ce;
  --line-strong: #c9c6ba;
  --accent: #6f8f2c;
  --accent-soft: #879a39;
  --warning: #100f0f;
  --shadow: 0 18px 40px rgba(16, 15, 15, 0.08);
  --overlay-color: rgba(16, 15, 15, 0.04);
  --screen-bg: linear-gradient(180deg, rgba(255, 252, 240, 0.98) 0%, rgba(246, 242, 230, 0.98) 100%);
  --screen-edge: rgba(16, 15, 15, 0.04);
  --panel-bg: linear-gradient(180deg, rgba(255, 252, 240, 0.96) 0%, rgba(246, 242, 230, 0.96) 100%);
  --search-bg: rgba(255, 252, 240, 0.92);
  --search-results-bg: rgba(255, 252, 240, 0.98);
  --property-bg: rgba(242, 240, 229, 0.72);
  --blockquote-bg: rgba(111, 143, 44, 0.07);
  --pre-bg: rgba(246, 242, 230, 0.96);
  --code-bg: rgba(16, 15, 15, 0.05);
  --command-bg: rgba(111, 143, 44, 0.07);
  --row-hover: rgba(16, 15, 15, 0.035);
  --probe-yellow: #ffef2e;
  --probe-blue: #2b83f6;
  --probe-red: #ff0e0e;
  --probe-purple: #5648ed;
  --button-shadow: 6px 5px 0 rgba(16, 15, 15, 0.16);
  --button-shadow-hover: 3px 2px 0 rgba(16, 15, 15, 0.12);
  --panel-shadow: 0 10px 24px rgba(16, 15, 15, 0.05);
  --island-bg: rgba(16, 15, 15, 0.05);
  --island-active-bg: #ffffff;
  --max: 1360px;
  --sans: -apple-system, BlinkMacSystemFont, Inter, "IBM Plex Sans", "Segoe UI", Helvetica, Arial, sans-serif;
  --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
}

html[data-theme="dark"] {
  --bg: #100f0f;
  --bg-soft: #1c1b1a;
  --surface: rgba(28, 27, 26, 0.96);
  --surface-strong: #282726;
  --surface-hover: #343331;
  --text: #cecdc3;
  --muted: #878580;
  --line: #343331;
  --line-strong: #403e3c;
  --accent: #8daa54;
  --accent-soft: #b7c96d;
  --warning: #f2f0e5;
  --shadow: 0 28px 80px rgba(0, 0, 0, 0.46);
  --overlay-color: rgba(255, 255, 255, 0.028);
  --screen-bg: linear-gradient(180deg, rgba(40, 39, 38, 0.98) 0%, rgba(16, 15, 15, 1) 100%);
  --screen-edge: rgba(242, 240, 229, 0.035);
  --panel-bg: linear-gradient(180deg, rgba(40, 39, 38, 0.96) 0%, rgba(28, 27, 26, 0.96) 100%);
  --search-bg: rgba(16, 15, 15, 0.75);
  --search-results-bg: rgba(16, 15, 15, 0.98);
  --property-bg: rgba(16, 15, 15, 0.35);
  --blockquote-bg: rgba(141, 170, 84, 0.06);
  --pre-bg: rgba(16, 15, 15, 0.95);
  --code-bg: rgba(255, 255, 255, 0.05);
  --command-bg: rgba(16, 15, 15, 0.45);
  --row-hover: rgba(255, 255, 255, 0.03);
  --probe-yellow: #ffef2e;
  --probe-blue: #70a7ff;
  --probe-red: #ff5454;
  --probe-purple: #7a72ff;
  --button-shadow: 6px 5px 0 rgba(0, 0, 0, 0.35);
  --button-shadow-hover: 3px 2px 0 rgba(0, 0, 0, 0.28);
  --panel-shadow: 0 16px 36px rgba(0, 0, 0, 0.18);
  --island-bg: rgba(255, 255, 255, 0.06);
  --island-active-bg: rgba(255, 239, 46, 0.12);
}

* {
  box-sizing: border-box;
}

html {
  color-scheme: light dark;
  background: var(--bg);
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: var(--sans);
  color: var(--text);
  background:
    radial-gradient(circle at top left, rgba(141, 170, 84, 0.14), transparent 18%),
    radial-gradient(circle at top right, rgba(16, 15, 15, 0.03), transparent 22%),
    linear-gradient(180deg, var(--bg) 0%, var(--bg-soft) 100%);
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0)),
    repeating-linear-gradient(
      180deg,
      var(--overlay-color) 0,
      var(--overlay-color) 1px,
      transparent 1px,
      transparent 4px
    );
  opacity: 1;
}

a {
  color: inherit;
}

.brand,
.brand-meta,
.subline,
.footer code,
.search-shell,
.micro,
.tab,
.button,
.tag,
.nav a,
.eyebrow,
.section-head h2,
.property-key,
.path,
.command,
code,
pre,
thead th {
  font-family: var(--mono);
}

.shell {
  width: min(calc(100% - 20px), var(--max));
  margin: 0 auto;
  padding: 10px 0 28px;
}

.screen {
  position: relative;
  overflow: hidden;
  min-height: calc(100vh - 40px);
  border: 1px solid var(--line-strong);
  background: var(--screen-bg);
  box-shadow: var(--shadow);
}

.screen::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border: 1px solid var(--screen-edge);
}

.screen::after {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--probe-red), var(--probe-yellow));
  pointer-events: none;
}

.topbar,
.tabbar,
.footer {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 16px;
  border-bottom: 1px solid var(--line);
}

.topbar {
  min-height: 54px;
}

.tabbar {
  min-height: 36px;
  overflow-x: auto;
  justify-content: flex-start;
  border-bottom: none;
}

.footer {
  min-height: 34px;
  border-top: 1px solid var(--line);
  border-bottom: none;
  color: var(--muted);
  font-size: 0.78rem;
}

.brandline,
.toolbar,
.tabset,
.subline,
.links {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tabset {
  width: fit-content;
  padding: 4px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--island-bg);
}

.toolbar {
  justify-content: flex-end;
  flex: 1;
}

.brand {
  color: var(--accent);
  font-size: 0.94rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.brand::before {
  content: "●";
  margin-right: 8px;
  color: var(--accent);
  animation: blink 1.2s steps(1) infinite;
}

.brand-meta,
.footer code,
.subline {
  color: var(--muted);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.brand::before {
  content: "*";
}

.search-shell {
  position: relative;
  display: grid;
  grid-template-columns: 24px minmax(180px, 320px);
  align-items: center;
  min-height: 36px;
  border: 2px solid var(--line-strong);
  background: var(--search-bg);
  box-shadow: var(--button-shadow);
}

.search-shell:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px rgba(141, 170, 84, 0.15);
  transform: translate(4px, 3px);
}

.search-prompt {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  font-size: 0.82rem;
  border-right: 1px solid var(--line);
}

.search-input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: none;
  padding: 7px 10px;
  background: transparent;
  color: var(--warning);
  font: inherit;
  font-size: 0.82rem;
}

.search-input::placeholder {
  color: var(--muted);
}

.search-results {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  width: min(640px, 78vw);
  max-height: 440px;
  overflow: auto;
  padding: 8px;
  border: 2px solid var(--line-strong);
  background: var(--search-results-bg);
  box-shadow: var(--shadow);
  z-index: 4;
}

.search-results[hidden] {
  display: none;
}

.search-result,
.results-empty {
  display: block;
  padding: 10px 12px;
  border: 1px solid transparent;
  text-decoration: none;
}

.search-result:hover {
  border-color: var(--line-strong);
  background: var(--surface-hover);
}

.search-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.search-type {
  color: var(--accent);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.search-title {
  color: var(--warning);
}

.search-summary,
.search-path {
  margin-top: 4px;
  color: var(--muted);
  font-size: 0.8rem;
  line-height: 1.45;
}

.micro,
.tab,
.button,
.tag,
.nav a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 12px;
  border: 2px solid var(--line-strong);
  background: var(--surface);
  color: var(--warning);
  text-decoration: none;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.72rem;
  white-space: nowrap;
  box-shadow: var(--button-shadow);
  transition: background 120ms ease, color 120ms ease, border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease;
}

.tab {
  min-height: 30px;
  border-color: transparent;
  border-radius: 999px;
  background: transparent;
  box-shadow: none;
}

button.micro {
  cursor: pointer;
  font: inherit;
}

.micro:hover,
.tab:hover,
.button:hover,
.tag:hover,
.nav a:hover,
.links a:hover {
  background: var(--surface-hover);
  color: var(--warning);
  box-shadow: var(--button-shadow-hover);
  transform: translate(3px, 2px);
}

.tab[data-state="active"] {
  border-color: var(--warning);
  background: var(--island-active-bg);
  color: var(--warning);
  box-shadow: none;
}

.theme-toggle {
  min-width: 72px;
}

.theme-toggle[aria-pressed="true"] {
  border-color: var(--probe-yellow);
  background: var(--probe-yellow);
  color: #100f0f;
  box-shadow: none;
}

.tab:hover {
  box-shadow: none;
  transform: none;
}

.workspace {
  position: relative;
  z-index: 1;
  padding: 18px 18px 24px;
}

.hero,
.panel,
.note,
.dataset-card,
.stat {
  background: var(--panel-bg);
  border: 2px solid var(--line-strong);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03), var(--panel-shadow);
}

.hero {
  padding: 26px;
  margin-bottom: 18px;
  position: relative;
  overflow: hidden;
}

.hero::after {
  content: "";
  position: absolute;
  top: 18px;
  right: 18px;
  width: 14px;
  height: 14px;
  border-radius: 3px;
  background: var(--probe-yellow);
  box-shadow: 18px 0 0 var(--probe-blue), 36px 0 0 var(--probe-red);
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  border: 2px solid var(--warning);
  background: var(--probe-yellow);
  color: #100f0f;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.hero h1,
.note h1 {
  margin: 14px 0 10px;
  font-size: clamp(2rem, 4vw, 4rem);
  line-height: 1.02;
  letter-spacing: -0.03em;
  color: var(--warning);
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
  font-size: 0.95rem;
  line-height: 1.7;
}

.muted,
.meta,
.note .meta {
  color: var(--muted);
}

.nav {
  display: contents;
}

.button {
  color: #100f0f;
  border-color: var(--probe-yellow);
  background: var(--probe-yellow);
}

.button.secondary {
  color: var(--warning);
  border-color: var(--line-strong);
  background: var(--surface);
}

.grid {
  display: grid;
  gap: 14px;
}

.grid.stats {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  margin-bottom: 18px;
}

.grid.cards,
.grid.datasets {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.stat,
.panel,
.dataset-card,
.note {
  padding: 18px;
}

.stat strong {
  display: block;
  font-size: 1.65rem;
  margin-bottom: 10px;
  color: var(--warning);
}

.grid.stats .stat:nth-child(4n + 1) {
  border-top-color: var(--probe-yellow);
}

.grid.stats .stat:nth-child(4n + 2) {
  border-top-color: var(--probe-blue);
}

.grid.stats .stat:nth-child(4n + 3) {
  border-top-color: var(--probe-red);
}

.grid.stats .stat:nth-child(4n + 4) {
  border-top-color: var(--accent);
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  margin: 0 0 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
}

.section-head h2 {
  margin: 0;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--warning);
}

.stack {
  display: grid;
  gap: 10px;
}

.note-layout {
  display: grid;
  grid-template-columns: minmax(0, 320px) minmax(0, 1fr);
  gap: 14px;
}

.sidebar-stack {
  display: grid;
  gap: 14px;
  align-self: start;
}

.sidebar {
  position: sticky;
  top: 16px;
  align-self: start;
}

.sidebar ul {
  list-style: none;
  padding: 0;
  margin: 10px 0 0;
  display: grid;
  gap: 6px;
}

.sidebar a {
  text-decoration: none;
  display: block;
  padding: 8px 10px;
  border: 1px solid var(--line);
  color: var(--muted);
}

.sidebar a:hover {
  border-color: var(--line-strong);
  color: var(--warning);
  background: var(--surface-hover);
}

.property-grid {
  display: grid;
  gap: 10px;
}

.property {
  padding: 10px 12px;
  border: 1px solid var(--line);
  background: var(--property-bg);
}

.property-key {
  margin-bottom: 6px;
  color: var(--accent);
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.property-value {
  color: var(--warning);
  font-size: 0.9rem;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.note h1,
.note h2,
.note h3,
.note h4,
.note h5,
.note h6 {
  line-height: 1.15;
  margin: 1.2em 0 0.5em;
  color: var(--warning);
}

.note h2 {
  font-size: 1.25rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.note h3 {
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
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
  border-left: 2px solid var(--accent);
  background: var(--blockquote-bg);
}

pre,
code {
  font-family: "Courier New", monospace;
}

pre {
  overflow-x: auto;
  padding: 14px 16px;
  border: 1px solid var(--line-strong);
  background: var(--pre-bg);
  color: var(--accent-soft);
}

code {
  padding: 0.15em 0.4em;
  background: var(--code-bg);
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
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--muted);
}

th,
td {
  padding: 10px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}

tbody tr:hover {
  background: var(--row-hover);
}

.note a,
.lede a,
.list-rows a {
  color: var(--probe-blue);
  font-weight: 700;
  text-decoration: underline;
}

.links {
  margin-top: 14px;
}

.links a {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border: 2px solid var(--line-strong);
  background: var(--surface);
  box-shadow: var(--button-shadow);
  text-decoration: none;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.72rem;
  color: var(--warning);
}

.path {
  font-family: "Courier New", monospace;
  font-size: 0.82rem;
  overflow-wrap: anywhere;
}

.lede {
  max-width: 76ch;
}

.split {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.9fr);
  gap: 14px;
}

.command {
  margin-top: 12px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  background: var(--command-bg);
  color: var(--accent-soft);
  font-size: 0.84rem;
}

.command::before {
  content: ">";
  margin-right: 8px;
  color: var(--accent);
}

.feed {
  display: grid;
  gap: 8px;
}

.feed-row {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr);
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--line);
}

.feed-time {
  color: var(--accent);
  font-size: 0.74rem;
  text-transform: uppercase;
}

.feed-body strong,
.dataset-card h3,
.panel h3 {
  color: var(--warning);
}

.dataset-card h3,
.panel h3 {
  margin: 0 0 10px;
  font-size: 1rem;
  line-height: 1.35;
}

.list-rows {
  display: grid;
  gap: 8px;
}

.list-rows div {
  padding: 8px 0;
  border-bottom: 1px solid var(--line);
}

.media-toolbar {
  display: grid;
  gap: 14px;
  margin-bottom: 18px;
}

.media-marquee {
  overflow: hidden;
  border: 2px solid var(--line-strong);
  background: var(--surface);
  box-shadow: var(--button-shadow);
}

.media-marquee-track {
  display: flex;
  gap: 20px;
  padding: 10px 14px;
  min-width: max-content;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.74rem;
}

.media-marquee-track strong {
  color: var(--warning);
}

.media-filterbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.media-filters,
.media-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.media-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 0 12px;
  border: 2px solid var(--line-strong);
  background: var(--surface);
  color: var(--warning);
  text-decoration: none;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.72rem;
  box-shadow: var(--button-shadow);
}

.media-chip:hover {
  transform: translate(3px, 2px);
  box-shadow: var(--button-shadow-hover);
}

.media-chip[data-tone="yellow"] {
  background: var(--probe-yellow);
  border-color: var(--probe-yellow);
  color: #100f0f;
}

.media-chip[data-tone="blue"] {
  border-color: var(--probe-blue);
}

.media-chip[data-tone="red"] {
  border-color: var(--probe-red);
}

.media-layout {
  display: grid;
  gap: 18px;
}

.media-section {
  display: grid;
  gap: 14px;
}

.media-intro {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.media-intro p {
  margin: 0;
}

.media-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.media-card {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 2px solid var(--line-strong);
  background: var(--panel-bg);
  box-shadow: var(--panel-shadow);
}

.media-card[data-kind="image"] {
  border-top-color: var(--probe-yellow);
}

.media-card[data-kind="video"] {
  border-top-color: var(--probe-blue);
}

.media-card[data-kind="file"] {
  border-top-color: var(--probe-red);
}

.media-thumb {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  border: 2px solid var(--line-strong);
  background:
    linear-gradient(135deg, rgba(111, 143, 44, 0.12), transparent 52%),
    linear-gradient(180deg, var(--surface-strong), var(--surface));
}

.media-thumb img,
.media-thumb video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.media-placeholder {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  color: var(--warning);
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.media-card h3 {
  margin: 0;
  color: var(--warning);
  font-size: 1rem;
}

.media-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.media-empty {
  padding: 20px;
  border: 2px dashed var(--line-strong);
  background: var(--surface);
  color: var(--muted);
}

.media-empty strong {
  color: var(--warning);
}

.table-wrap {
  overflow-x: auto;
}

.stack-list,
.timeline-list,
.rank-list,
.facts {
  display: grid;
  gap: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 14px;
}

.metric-card {
  padding: 16px;
  border: 1px solid var(--line);
  background: var(--surface);
  box-shadow: var(--panel-shadow);
}

.metric-card strong {
  display: block;
  font-size: 1.35rem;
  color: var(--warning);
}

.metric-card span {
  color: var(--muted);
  font-size: 0.82rem;
}

.analytics-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 24px;
}

.directory-grid,
.workstream-grid,
.proposal-grid,
.spotlight-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}

.entity-card,
.rank-card {
  padding: 18px;
  border: 1px solid var(--line);
  background: var(--surface);
  box-shadow: var(--panel-shadow);
}

.entity-card h3,
.rank-card h3 {
  margin: 0 0 8px;
}

.pill-row,
.filter-row,
.inline-links {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pill {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--line-strong);
  background: var(--surface-strong);
  color: var(--warning);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.pill.muted {
  color: var(--muted);
}

.filter-chip {
  cursor: pointer;
}

.filter-chip[data-state="active"] {
  border-color: var(--warning);
  background: var(--probe-yellow);
  color: #100f0f;
}

.identity-block {
  display: grid;
  gap: 14px;
}

.identity-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 0.82rem;
}

.section-stack {
  display: grid;
  gap: 24px;
}

.panel-list {
  display: grid;
  gap: 14px;
}

.timeline-item,
.fact-row,
.rank-row {
  display: grid;
  gap: 6px;
  padding: 14px 0;
  border-top: 1px solid var(--line);
}

.timeline-item:first-child,
.fact-row:first-child,
.rank-row:first-child {
  border-top: 0;
  padding-top: 0;
}

.timeline-date,
.rank-value {
  color: var(--muted);
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.hero-rail {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 14px;
}

.kicker {
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.8rem;
}

.entity-card[hidden] {
  display: none !important;
}

.flash {
  color: var(--accent);
}

@keyframes blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0.35; }
}

@media (max-width: 1040px) {
  .topbar {
    align-items: flex-start;
    padding-top: 10px;
    padding-bottom: 10px;
  }

  .brandline,
  .toolbar {
    width: 100%;
  }

  .toolbar {
    justify-content: flex-start;
  }

  .search-shell {
    width: min(100%, 520px);
    grid-template-columns: 24px minmax(0, 1fr);
  }
}

@media (max-width: 900px) {
  .analytics-grid,
  .note-layout,
  .split {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
  }
}

@media (max-width: 640px) {
  .workspace {
    padding: 12px;
  }

  .topbar,
  .tabbar,
  .footer {
    padding-left: 10px;
    padding-right: 10px;
  }

  .hero h1,
  .note h1 {
    font-size: 1.7rem;
  }

  .search-results {
    width: min(100vw - 36px, 520px);
  }
}
"""


SEARCH_JS = r"""
(function () {
  const themeToggle = document.querySelector("[data-theme-toggle]");
  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

  const applyTheme = (theme, persist = false) => {
    document.documentElement.dataset.theme = theme;

    if (themeToggle) {
      themeToggle.textContent = theme === "dark" ? "Light" : "Dark";
      themeToggle.setAttribute("aria-pressed", String(theme === "dark"));
      themeToggle.setAttribute(
        "aria-label",
        theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
      );
    }

    if (persist) {
      try {
        localStorage.setItem("gnars-theme", theme);
      } catch (error) {
        // Ignore storage failures and keep the in-memory theme.
      }
    }
  };

  const resolveTheme = () => {
    try {
      return localStorage.getItem("gnars-theme") || (mediaQuery.matches ? "dark" : "light");
    } catch (error) {
      return mediaQuery.matches ? "dark" : "light";
    }
  };

  applyTheme(resolveTheme());
  themeToggle?.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(nextTheme, true);
  });

  mediaQuery.addEventListener?.("change", () => {
    try {
      if (localStorage.getItem("gnars-theme")) {
        return;
      }
    } catch (error) {
      // Ignore storage failures and fall back to the system theme.
    }
    applyTheme(mediaQuery.matches ? "dark" : "light");
  });

  const root = document.querySelector("[data-search-root]");
  if (!root) return;

  const input = root.querySelector("[data-search-input]");
  const results = root.querySelector("[data-search-results]");
  const indexUrl = root.dataset.indexUrl;
  const siteRoot = (root.dataset.siteRoot || ".").replace(/\/+$/, "") || ".";
  let searchIndexPromise = null;
  let timer = 0;

  const escapeHtml = (value) =>
    String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const resolveHref = (href) => {
    const prefix = siteRoot === "." ? "." : siteRoot;
    return `${prefix}/${href}`.replace(/\\/g, "/").replace(/\/{2,}/g, "/");
  };

  const loadIndex = async () => {
    if (!searchIndexPromise) {
      searchIndexPromise = fetch(indexUrl)
        .then((response) => {
          if (!response.ok) throw new Error(`search index: ${response.status}`);
          return response.json();
        })
        .catch(() => []);
    }
    return searchIndexPromise;
  };

  const scoreEntry = (entry, tokens) => {
    const title = String(entry.title || "").toLowerCase();
    const summary = String(entry.summary || "").toLowerCase();
    const path = String(entry.path || "").toLowerCase();
    const searchText = String(entry.search_text || "").toLowerCase();
    const haystack = `${title} ${summary} ${path} ${searchText}`;
    let score = 0;

    for (const token of tokens) {
      if (!haystack.includes(token)) return 0;
      if (title.includes(token)) score += 6;
      if (path.includes(token)) score += 3;
      if (summary.includes(token)) score += 2;
      score += 1;
    }

    return score;
  };

  const renderResults = (entries, query) => {
    if (!query.trim()) {
      results.hidden = true;
      results.innerHTML = "";
      return;
    }

    if (!entries.length) {
      results.hidden = false;
      results.innerHTML = `<div class="results-empty">No matches for "${escapeHtml(query)}".</div>`;
      return;
    }

    results.hidden = false;
    results.innerHTML = entries
      .map(
        (entry) => `
          <a class="search-result" href="${escapeHtml(resolveHref(entry.href))}">
            <div class="search-head">
              <strong class="search-title">${escapeHtml(entry.title || "Untitled")}</strong>
              <span class="search-type">${escapeHtml(entry.type || "page")}</span>
            </div>
            <div class="search-summary">${escapeHtml(entry.summary || "")}</div>
            <div class="search-path">${escapeHtml(entry.path || entry.href || "")}</div>
          </a>
        `
      )
      .join("");
  };

  const runSearch = async (query) => {
    const tokens = query
      .toLowerCase()
      .split(/\\s+/)
      .map((token) => token.trim())
      .filter(Boolean);

    if (!tokens.length) {
      renderResults([], "");
      return;
    }

    const index = await loadIndex();
    const ranked = index
      .map((entry) => ({ entry, score: scoreEntry(entry, tokens) }))
      .filter((entry) => entry.score > 0)
      .sort((left, right) => right.score - left.score)
      .slice(0, 8)
      .map((entry) => entry.entry);

    renderResults(ranked, query);
  };

  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = window.setTimeout(() => {
      void runSearch(input.value);
    }, 80);
  });

  input.addEventListener("focus", () => {
    if (input.value.trim()) {
      void runSearch(input.value);
    }
  });

  document.addEventListener("click", (event) => {
    if (!root.contains(event.target)) {
      results.hidden = true;
    }
  });

  document.addEventListener("keydown", (event) => {
    const tagName = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
    const isEditable = tagName === "input" || tagName === "textarea";

    if (event.key === "/" && !isEditable) {
      event.preventDefault();
      input.focus();
      input.select();
    }

    if (event.key === "Escape") {
      results.hidden = true;
      if (document.activeElement === input) {
        input.blur();
      }
    }
  });
})();

(() => {
  document.querySelectorAll("[data-filter-root]").forEach((root) => {
    const cards = Array.from(root.querySelectorAll("[data-filter-tags]"));
    const buttons = Array.from(root.querySelectorAll("[data-filter-value]"));
    if (!cards.length || !buttons.length) return;

    const applyFilter = (value) => {
      buttons.forEach((button) => {
        button.dataset.state = button.dataset.filterValue === value ? "active" : "idle";
      });

      cards.forEach((card) => {
        const tags = String(card.dataset.filterTags || "")
          .split(/\s+/)
          .map((item) => item.trim())
          .filter(Boolean);
        const visible = value === "all" || tags.includes(value);
        card.hidden = !visible;
      });
    };

    buttons.forEach((button) => {
      button.addEventListener("click", () => applyFilter(button.dataset.filterValue || "all"));
    });

    applyFilter(root.dataset.defaultFilter || "all");
  });
})();
"""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def site_relative(path: Path) -> str:
    return path.relative_to(SITE_DIR).as_posix()


def rel_href(from_page: Path, to_page: Path) -> str:
    return posixpath.relpath(site_relative(to_page), start=site_relative(from_page.parent))


def active_section(path: Path) -> str:
    relative = site_relative(path)
    if relative.startswith("people/"):
        return "people"
    if relative.startswith("workstreams/"):
        return "workstreams"
    if relative.startswith("treasury/"):
        return "treasury"
    if relative.startswith("proposals/"):
        return "proposals"
    if relative.startswith("notes/"):
        return "notes"
    if relative.startswith("datasets/"):
        return "datasets"
    if relative.startswith("media/") and relative.endswith(".html"):
        return "media"
    return "home"


def html_document(path: Path, *, title: str, body: str, description: str = "") -> str:
    css_href = rel_href(path, SITE_DIR / "assets" / "site.css")
    search_js_href = rel_href(path, SITE_DIR / "assets" / "search.js")
    search_index_href = rel_href(path, SITE_DIR / "assets" / "search-index.json")
    home_href = rel_href(path, SITE_DIR / "index.html")
    people_href = rel_href(path, people_index_path())
    workstreams_href = rel_href(path, workstreams_index_path())
    treasury_href = rel_href(path, treasury_page_path())
    proposals_href = rel_href(path, proposals_index_path())
    notes_href = rel_href(path, SITE_DIR / "notes" / "index.html")
    datasets_href = rel_href(path, SITE_DIR / "datasets" / "index.html")
    media_href = rel_href(path, SITE_DIR / "media" / "index.html")
    people_csv_href = rel_href(path, SITE_DIR / "exports" / "people.csv")
    spend_csv_href = rel_href(path, SITE_DIR / "exports" / "spend_ledger.csv")
    current = active_section(path)
    site_root = posixpath.relpath(".", start=site_relative(path.parent))

    def tab(href: str, label: str, section_name: str | None = None) -> str:
        state = ' data-state="active"' if section_name is not None and section_name == current else ""
        return f'<a class="tab" href="{href}"{state}>{label}</a>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}" />
  <script>
    (() => {{
      try {{
        const stored = localStorage.getItem("gnars-theme");
        const theme = stored || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
        document.documentElement.dataset.theme = theme;
      }} catch (error) {{
        document.documentElement.dataset.theme = "light";
      }}
    }})();
  </script>
  <link rel="stylesheet" href="{css_href}" />
</head>
<body>
  <div class="shell">
    <div class="screen">
      <div class="topbar">
        <div class="brandline">
          <span class="brand">GNARS.DATA</span>
          <span class="brand-meta">project terminal / github pages</span>
        </div>
        <div class="toolbar">
          <div class="search-shell" data-search-root data-index-url="{search_index_href}" data-site-root="{site_root}">
            <span class="search-prompt">/</span>
            <input class="search-input" type="search" placeholder="search people, workstreams, proposals, data..." data-search-input />
            <div class="search-results" data-search-results hidden></div>
          </div>
          <button class="micro theme-toggle" type="button" data-theme-toggle aria-pressed="false">Dark</button>
          <a class="micro" href="{people_csv_href}">people.csv</a>
          <a class="micro" href="{spend_csv_href}">spend_ledger.csv</a>
        </div>
      </div>
      <div class="tabbar">
        <div class="tabset">
          {tab(home_href, "OVERVIEW", "home")}
          {tab(people_href, "PEOPLE", "people")}
          {tab(workstreams_href, "WORKSTREAMS", "workstreams")}
          {tab(treasury_href, "TREASURY", "treasury")}
          {tab(proposals_href, "PROPOSALS", "proposals")}
          {tab(notes_href, "NOTES", "notes")}
          {tab(datasets_href, "DATA", "datasets")}
          {tab(media_href, "MEDIA", "media")}
        </div>
      </div>
      <div class="workspace">
        {body}
      </div>
      <div class="footer">
        <div class="subline">gnars camp / analytics-first dao archive / static pages</div>
        <div>tracked in <code>gnars-data</code> with public csv + json endpoints</div>
      </div>
    </div>
  </div>
  <script src="{search_js_href}" defer></script>
</body>
</html>
"""


def load_json(name: str) -> Any:
    with (DATA_DIR / f"{name}.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def short_address(address: str | None) -> str:
    if not address:
        return "unknown"
    if len(address) < 12:
        return address
    return f"{address[:6]}...{address[-4:]}"


def format_number(value: Any, digits: int = 0) -> str:
    if value in (None, ""):
        return "n/a"
    if digits == 0:
        return f"{float(value):,.0f}"
    return f"{float(value):,.{digits}f}"


def format_pct(value: Any) -> str:
    if value in (None, ""):
        return "n/a"
    return f"{float(value):.0f}%"


def format_asset(value: Any, symbol: str, digits: int = 2) -> str:
    if value in (None, ""):
        return f"0 {symbol}"
    return f"{float(value):,.{digits}f} {symbol}"


def normalize_address(address: str | None) -> str:
    return (address or "").strip().lower()


def join_pills(values: list[str], *, muted: bool = False) -> str:
    if not values:
        return '<span class="pill muted">none</span>' if muted else ""
    return "".join(
        f'<span class="pill{" muted" if muted else ""}">{html.escape(str(value))}</span>'
        for value in values
        if str(value).strip()
    )


def table_panel(title: str, headers: list[str], rows: list[dict[str, Any]], meta: str = "") -> str:
    meta_html = f'<span class="meta">{html.escape(meta)}</span>' if meta else ""
    return f"""
    <div class="panel">
      <div class="section-head">
        <h2>{html.escape(title)}</h2>
        {meta_html}
      </div>
      <div class="table-wrap">
        {render_table(headers, rows)}
      </div>
    </div>
    """


def truncate(value: str, limit: int = 160) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def clamp_text(value: str, limit: int = 160) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    if len(cleaned) <= limit:
        return cleaned
    if limit <= 3:
        return cleaned[:limit]
    return cleaned[: limit - 3].rstrip() + "..."


def truncate(value: str, limit: int = 160) -> str:
    return clamp_text(value, limit)


def normalize_property_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    if value is None:
        return ""
    return str(value).strip()


def compact_properties(properties: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {}
    for key, value in properties.items():
        if isinstance(value, list):
            items = [str(item).strip() for item in value if str(item).strip()]
            if items:
                compacted[key] = items
            continue
        text = normalize_property_value(value)
        if text:
            compacted[key] = text
    return compacted


def parse_frontmatter(markdown_text: str) -> tuple[dict[str, Any], str]:
    normalized = markdown_text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return {}, markdown_text

    lines = normalized.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, markdown_text

    properties: dict[str, Any] = {}
    current_key: str | None = None

    for index in range(1, len(lines)):
        raw_line = lines[index]
        stripped = raw_line.strip()

        if stripped == "---":
            body = "\n".join(lines[index + 1 :]).lstrip("\n")
            return compact_properties(properties), body

        if not stripped:
            continue

        list_match = re.match(r"^\s*-\s+(.*)$", raw_line)
        if list_match and current_key:
            current_value = properties.get(current_key)
            if not isinstance(current_value, list):
                current_value = [] if current_value in (None, "") else [str(current_value)]
            current_value.append(list_match.group(1).strip().strip('"').strip("'"))
            properties[current_key] = current_value
            continue

        pair_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", stripped)
        if pair_match:
            key, value = pair_match.groups()
            current_key = key
            if value:
                properties[key] = value.strip().strip('"').strip("'")
            else:
                properties[key] = []
            continue

        if current_key and isinstance(properties.get(current_key), list):
            properties[current_key].append(stripped)

    return {}, markdown_text


def markdown_plain_text(markdown_text: str) -> str:
    text = re.sub(r"```.*?```", " ", markdown_text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"^[>#-]+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"#{1,6}\s*", "", text)
    return re.sub(r"\s+", " ", text).strip()


def render_properties(properties: dict[str, Any]) -> str:
    if not properties:
        return '<p class="muted">No properties available.</p>'

    cards = []
    for key, value in properties.items():
        cards.append(
            f"""
            <div class="property">
              <div class="property-key">{html.escape(key)}</div>
              <div class="property-value">{html.escape(normalize_property_value(value))}</div>
            </div>
            """
        )
    return f'<div class="property-grid">{"".join(cards)}</div>'


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
            return clamp_text(stripped, limit=180)
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
        *sorted((ROOT / "media").rglob("*.md")),
        *sorted((ROOT / "reports").rglob("*.md")),
    ]

    notes = []
    for path in note_paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter, body_text = parse_frontmatter(text)
        relative_source = path.relative_to(ROOT).as_posix()
        section = relative_source.split("/", 1)[0] if "/" in relative_source else "root"
        folder = path.relative_to(ROOT).parent.as_posix()
        default_title = path.stem.replace("-", " ").title()
        title = normalize_property_value(frontmatter.get("title")) or note_title(body_text, default_title)
        summary = (
            normalize_property_value(frontmatter.get("summary"))
            or normalize_property_value(frontmatter.get("description"))
            or note_summary(body_text)
        )
        properties = compact_properties(
            {
                **frontmatter,
                "kind": "note",
                "section": section,
                "folder": folder if folder != "." else "root",
                "path": relative_source,
            }
        )
        plain_text = markdown_plain_text(body_text)
        notes.append(
            {
                "source": path,
                "relative_source": relative_source,
                "title": title,
                "summary": summary,
                "html": render_markdown(body_text),
                "body_text": body_text,
                "properties": properties,
                "search_text": " ".join(
                    part
                    for part in [
                        title,
                        summary,
                        " ".join(normalize_property_value(value) for value in properties.values()),
                        plain_text,
                    ]
                    if part
                ),
                "output": note_output_path(path),
            }
        )
    return notes


def proposal_display_title(record: dict[str, Any]) -> str:
    raw_title = (record.get("title") or "").strip()
    if not raw_title:
        return record.get("archive_id", "untitled")
    first_line = raw_title.splitlines()[0].strip()
    return first_line.lstrip("#").strip() or raw_title


def preview_cell(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return clamp_text(json.dumps(value, ensure_ascii=False), limit=120)
    return clamp_text(str(value), limit=120)


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


def people_index_path() -> Path:
    return SITE_DIR / "people" / "index.html"


def person_page_path(slug: str) -> Path:
    return SITE_DIR / "people" / slug / "index.html"


def workstreams_index_path() -> Path:
    return SITE_DIR / "workstreams" / "index.html"


def workstream_page_path(slug: str) -> Path:
    return SITE_DIR / "workstreams" / slug / "index.html"


def treasury_page_path() -> Path:
    return SITE_DIR / "treasury" / "index.html"


def proposals_index_path() -> Path:
    return SITE_DIR / "proposals" / "index.html"


def proposal_page_path(archive_id: str) -> Path:
    return SITE_DIR / "proposals" / archive_id / "index.html"


def media_index_path() -> Path:
    return SITE_DIR / "media" / "index.html"


def media_title(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").title()


def media_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in MEDIA_IMAGE_EXTENSIONS:
        return "image"
    if suffix in MEDIA_VIDEO_EXTENSIONS:
        return "video"
    return "file"


def discover_media_library() -> dict[str, Any]:
    categories_config = [
        ("assets", "Brand Assets", "Logos, proposal banners, social cards, and shared design kits."),
        ("photos", "Photos", "Event photography, production stills, and campaign documentation."),
        ("videos", "Videos", "Clips, edits, promos, interviews, and archive footage."),
    ]

    categories: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    for slug, title, fallback_summary in categories_config:
        directory = MEDIA_DIR / slug
        readme_path = directory / "README.md"
        summary = fallback_summary

        if readme_path.exists():
            readme_text = readme_path.read_text(encoding="utf-8")
            _, readme_body = parse_frontmatter(readme_text)
            summary = note_summary(readme_body)

        category_items: list[dict[str, Any]] = []
        if directory.exists():
            for path in sorted(directory.rglob("*")):
                if not path.is_file():
                    continue
                if path.name == ".gitkeep" or path.name.lower() == "readme.md":
                    continue

                relative_source = path.relative_to(ROOT).as_posix()
                kind = media_kind(path)
                item = {
                    "title": media_title(path),
                    "kind": kind,
                    "category": slug,
                    "relative_source": relative_source,
                    "summary": f"{title} asset published under `{relative_source}`.",
                }
                category_items.append(item)
                items.append(item)

        categories.append(
            {
                "slug": slug,
                "title": title,
                "summary": summary,
                "items": category_items,
                "count": len(category_items),
            }
        )

    return {
        "categories": categories,
        "items": items,
        "total_count": len(items),
    }


def load_analytics() -> dict[str, Any]:
    analytics = {
        "people": load_json("people"),
        "project_updates": load_json("project_updates"),
        "project_rollups": load_json("project_rollups"),
        "spend_ledger": load_json("spend_ledger"),
        "dao_metrics": load_json("dao_metrics"),
        "proposals_archive": load_json("proposals_archive"),
        "treasury": load_json("treasury"),
        "proposal_tags": load_json("proposal_tags"),
    }
    analytics["people_by_address"] = {
        normalize_address(record["address"]): record for record in analytics["people"]["records"]
    }
    analytics["project_by_id"] = {
        record["project_id"]: record for record in analytics["project_rollups"]["records"]
    }
    analytics["proposal_by_archive_id"] = {
        record["archive_id"]: record for record in analytics["proposals_archive"]["records"]
    }
    return analytics


def build_search_index(
    notes: list[dict[str, Any]],
    media_library: dict[str, Any],
    analytics: dict[str, Any],
) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []

    for note in notes:
        entries.append(
            {
                "type": "note",
                "title": note["title"],
                "summary": note["summary"],
                "href": site_relative(note["output"]),
                "path": note["relative_source"],
                "search_text": note.get("search_text", ""),
            }
        )

    for path in sorted(DATA_DIR.glob("*.json")):
        headers, _, metadata = json_preview(path)
        metadata_text = " ".join(f"{key} {normalize_property_value(value)}" for key, value in metadata.items())
        entries.append(
            {
                "type": "json",
                "title": path.name,
                "summary": "Canonical structured dataset published under /data/.",
                "href": site_relative(dataset_page_path("data", path)),
                "path": f"data/{path.name}",
                "search_text": " ".join([path.stem.replace("-", " "), " ".join(headers), metadata_text]).strip(),
            }
        )

    for path in sorted(EXPORTS_DIR.glob("*.csv")):
        headers, _ = csv_preview(path)
        entries.append(
            {
                "type": "csv",
                "title": path.name,
                "summary": "Downloadable export published under /exports/.",
                "href": site_relative(dataset_page_path("exports", path)),
                "path": f"exports/{path.name}",
                "search_text": " ".join([path.stem.replace("-", " "), " ".join(headers)]).strip(),
            }
        )

    for item in media_library["items"]:
        entries.append(
            {
                "type": item["kind"],
                "title": item["title"],
                "summary": item["summary"],
                "href": item["relative_source"],
                "path": item["relative_source"],
                "search_text": f"{item['title']} {item['category']} {item['kind']}",
            }
        )

    for person in analytics["people"]["records"]:
        entries.append(
            {
                "type": "person",
                "title": person["display_name"],
                "summary": clamp_text(
                    f"{person['role']} | {', '.join(person['tags'][:4])} | ETH {person['receipts']['eth_received']} | USDC {person['receipts']['usdc_received']}",
                    limit=160,
                ),
                "href": site_relative(person_page_path(person["slug"])),
                "path": f"people/{person['slug']}",
                "search_text": " ".join(
                    [
                        person["display_name"],
                        person["address"],
                        person["role"],
                        " ".join(person["tags"]),
                        " ".join(person["domains"]),
                    ]
                ).strip(),
            }
        )

    for project in analytics["project_rollups"]["records"]:
        entries.append(
            {
                "type": "workstream",
                "title": project["name"],
                "summary": clamp_text(
                    f"{project['status']} | spent {project['spent']['eth']} ETH / {project['spent']['usdc']} USDC | {project['updates_count']} updates",
                    limit=160,
                ),
                "href": site_relative(workstream_page_path(project["slug"])),
                "path": f"workstreams/{project['slug']}",
                "search_text": " ".join(
                    [
                        project["name"],
                        project["project_id"],
                        project["category"],
                        " ".join(project["origin_proposals"]),
                        " ".join(project["outputs"]),
                    ]
                ).strip(),
            }
        )

    for proposal in analytics["proposals_archive"]["records"]:
        entries.append(
            {
                "type": "proposal",
                "title": proposal_display_title(proposal),
                "summary": clamp_text(
                    f"{proposal['status']} | proposer {proposal.get('proposer_label') or short_address(proposal.get('proposer'))} | votes {len(proposal['votes'])}",
                    limit=160,
                ),
                "href": site_relative(proposal_page_path(proposal["archive_id"])),
                "path": f"proposals/{proposal['archive_id']}",
                "search_text": " ".join(
                    [
                        proposal_display_title(proposal),
                        proposal["archive_id"],
                        str(proposal.get("proposal_number") or ""),
                        proposal["status"],
                        str(proposal.get("proposer") or ""),
                    ]
                ).strip(),
            }
        )

    return entries


def build_home(notes: list[dict[str, Any]], media_library: dict[str, Any], analytics: dict[str, Any]) -> None:
    metrics = analytics["dao_metrics"]
    overview = metrics["overview"]
    people = analytics["people"]["records"]
    workstreams = analytics["project_rollups"]["records"]

    recent_proposal_rows = [
        {
            "proposal": f"P{record['proposal_number']}" if record.get("proposal_number") is not None else record["archive_id"],
            "title": proposal_display_title(analytics["proposal_by_archive_id"].get(record["archive_id"], record)),
            "status": record["status"],
            "end_at": record["end_at"],
        }
        for record in metrics["recent"]["proposals"][:6]
    ]
    recent_payout_rows = [
        {
            "recipient": record["recipient_display_name"],
            "asset": record["asset_symbol"],
            "amount": record["amount"],
            "project": record["project_id"] or "unassigned",
        }
        for record in metrics["recent"]["payouts"][:6]
    ]

    leaderboard_cards = []
    leaderboard_map = [
        ("USDC received", metrics["leaderboards"]["usdc_received"][:5], "USDC"),
        ("ETH received", metrics["leaderboards"]["eth_received"][:5], "ETH"),
        ("Active votes", metrics["leaderboards"]["active_votes"][:5], "votes"),
    ]
    for label, rows, suffix in leaderboard_map:
        items = []
        for row in rows:
            href = rel_href(SITE_DIR / "index.html", person_page_path(row["slug"]))
            value = format_number(row["value"], 2 if suffix in {"USDC", "ETH"} else 0)
            items.append(
                f"""
                <div class="rank-row">
                  <a href="{href}"><strong>{html.escape(row['display_name'])}</strong></a>
                  <span class="rank-value">{value} {html.escape(suffix)}</span>
                </div>
                """
            )
        leaderboard_cards.append(
            f"""
            <div class="panel">
              <div class="section-head">
                <h2>{html.escape(label)}</h2>
                <span class="meta">top 5</span>
              </div>
              <div class="rank-list">
                {''.join(items) or '<p class="muted">No rows yet.</p>'}
              </div>
            </div>
            """
        )

    spotlight_cards = []
    for row in metrics["leaderboards"]["usdc_received"][:4]:
        person = analytics["people_by_address"].get(normalize_address(row["address"]))
        if not person:
            continue
        href = rel_href(SITE_DIR / "index.html", person_page_path(person["slug"]))
        spotlight_cards.append(
            f"""
            <article class="entity-card">
              <div class="kicker">Recipient</div>
              <h3><a href="{href}">{html.escape(person['display_name'])}</a></h3>
              <p class="muted">{html.escape(person['role'])}</p>
              <div class="pill-row">{join_pills(person['tags'][:4], muted=True)}</div>
              <div class="identity-meta">
                <span>{format_asset(person['receipts']['eth_received'], 'ETH')}</span>
                <span>{format_asset(person['receipts']['usdc_received'], 'USDC')}</span>
                <span>{person['governance']['active_votes']} active votes</span>
              </div>
            </article>
            """
        )

    workstream_cards = []
    for project in workstreams[:4]:
        href = rel_href(SITE_DIR / "index.html", workstream_page_path(project["slug"]))
        workstream_cards.append(
            f"""
            <article class="entity-card">
              <div class="kicker">{html.escape(project['category'])}</div>
              <h3><a href="{href}">{html.escape(project['name'])}</a></h3>
              <p class="muted">{html.escape(project['objective'])}</p>
              <div class="identity-meta">
                <span>{format_asset(project['spent']['eth'], 'ETH')}</span>
                <span>{format_asset(project['spent']['usdc'], 'USDC')}</span>
                <span>{project['updates_count']} updates</span>
              </div>
            </article>
            """
        )

    note_cards = []
    for note in notes[:4]:
        href = rel_href(SITE_DIR / "index.html", note["output"])
        note_cards.append(
            f"""
            <article class="entity-card">
              <div class="kicker">{html.escape(note['relative_source'].split('/')[0])}</div>
              <h3><a href="{href}">{html.escape(note['title'])}</a></h3>
              <p class="muted">{html.escape(note['summary'])}</p>
            </article>
            """
        )

    media_cards = []
    for category in media_library["categories"]:
        media_cards.append(
            f"""
            <article class="entity-card">
              <div class="kicker">{html.escape(category['title'])}</div>
              <h3>{category['count']} items</h3>
              <p class="muted">{html.escape(category['summary'])}</p>
              <div class="inline-links">
                <a href="{rel_href(SITE_DIR / 'index.html', media_index_path())}#{html.escape(category['slug'])}">Open media</a>
              </div>
            </article>
            """
        )

    exports_panel = []
    for filename in ["people.csv", "spend_ledger.csv", "project_rollups.csv", "dao_metrics.csv", "proposals_archive.csv"]:
        path = EXPORTS_DIR / filename
        if not path.exists():
            continue
        href = rel_href(SITE_DIR / "index.html", SITE_DIR / "exports" / filename)
        preview_href = rel_href(SITE_DIR / "index.html", dataset_page_path("exports", path))
        exports_panel.append(
            f"""
            <article class="entity-card">
              <div class="kicker">Export</div>
              <h3>{html.escape(filename)}</h3>
              <div class="inline-links">
                <a href="{preview_href}">Preview</a>
                <a href="{href}">Download</a>
              </div>
            </article>
            """
        )

    body = f"""
    <div class="hero">
      <div class="eyebrow">Gnars Camp</div>
      <h1>DAO analytics, people, workstreams and treasury in a public terminal vault.</h1>
      <p class="lede">A nouns.camp-style surface for Gnars DAO that keeps the Quartz notes base intact while promoting real governance, budget, recipient and member analytics to the front page.</p>
      <div class="command">open /people /workstreams /treasury /proposals</div>
      <div class="hero-rail">
        <a class="button" href="{rel_href(SITE_DIR / 'index.html', people_index_path())}">Explore people</a>
        <a class="button secondary" href="{rel_href(SITE_DIR / 'index.html', workstreams_index_path())}">View workstreams</a>
        <a class="button secondary" href="{rel_href(SITE_DIR / 'index.html', treasury_page_path())}">Open treasury</a>
        <a class="button secondary" href="{rel_href(SITE_DIR / 'index.html', proposals_index_path())}">Browse proposals</a>
      </div>
    </div>

    <div class="metric-grid">
      <div class="metric-card"><strong>{overview['proposal_count']}</strong><span>proposals indexed</span></div>
      <div class="metric-card"><strong>{overview['people_count']}</strong><span>people in the unified directory</span></div>
      <div class="metric-card"><strong>{overview['workstream_count']}</strong><span>tracked workstreams</span></div>
      <div class="metric-card"><strong>${format_number(overview['treasury_total_value_usd'])}</strong><span>treasury holdings snapshot</span></div>
      <div class="metric-card"><strong>{format_asset(overview['outflows_eth'], 'ETH')}</strong><span>fungible ETH outflows</span></div>
      <div class="metric-card"><strong>{format_asset(overview['outflows_usdc'], 'USDC')}</strong><span>fungible USDC outflows</span></div>
      <div class="metric-card"><strong>{overview['contributors_count']}</strong><span>contributors / recipients</span></div>
      <div class="metric-card"><strong>{overview['athletes_count']}</strong><span>athlete-tagged profiles</span></div>
    </div>

    <div class="analytics-grid" style="margin-top: 24px;">
      <div class="section-stack">
        {table_panel("Recent proposals", ["proposal", "title", "status", "end_at"], recent_proposal_rows, "activity lane")}
        {table_panel("Recent payouts", ["recipient", "asset", "amount", "project"], recent_payout_rows, "fungible transfers only")}
      </div>
      <div class="section-stack">
        {''.join(leaderboard_cards)}
      </div>
    </div>

    <div class="panel" style="margin-top: 24px;">
      <div class="section-head">
        <h2>People spotlight</h2>
        <span class="meta">top recipients and active operators</span>
      </div>
      <div class="spotlight-grid">
        {''.join(spotlight_cards)}
      </div>
    </div>

    <div class="panel" style="margin-top: 24px;">
      <div class="section-head">
        <h2>Workstreams</h2>
        <span class="meta">budget vs spent, recipients and updates</span>
      </div>
      <div class="workstream-grid">
        {''.join(workstream_cards)}
      </div>
    </div>

    <div class="split" style="margin-top: 24px;">
      <div class="panel">
        <div class="section-head">
          <h2>Treasury snapshot</h2>
          <span class="meta">{overview['treasury_assets_count']} assets</span>
        </div>
        <div class="facts">
          {''.join(
              f'<div class="fact-row"><strong>{html.escape(asset["symbol"])}</strong><span>{html.escape(asset["name"])} | ${format_number(asset["value_usd"])}</span></div>'
              for asset in metrics["treasury"]["assets"][:6]
          )}
        </div>
      </div>
      <div class="panel">
        <div class="section-head">
          <h2>Publishing utility</h2>
          <span class="meta">downloads and machine endpoints</span>
        </div>
        <div class="panel-list">
          <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'exports' / 'people.csv')}">/exports/people.csv</a></div>
          <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'exports' / 'spend_ledger.csv')}">/exports/spend_ledger.csv</a></div>
          <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'exports' / 'project_rollups.csv')}">/exports/project_rollups.csv</a></div>
          <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'data' / 'people.json')}">/data/people.json</a></div>
          <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'data' / 'dao_metrics.json')}">/data/dao_metrics.json</a></div>
        </div>
      </div>
    </div>

    <div class="panel" style="margin-top: 24px;">
      <div class="section-head">
        <h2>Notes</h2>
        <span class="meta">Quartz markdown remains the long-form knowledge base</span>
      </div>
      <div class="spotlight-grid">
        {''.join(note_cards)}
      </div>
    </div>

    <div class="panel" style="margin-top: 24px;">
      <div class="section-head">
        <h2>Media</h2>
        <span class="meta">{media_library['total_count']} published assets</span>
      </div>
      <div class="spotlight-grid">
        {''.join(media_cards)}
      </div>
    </div>

    <div class="panel" style="margin-top: 24px;">
      <div class="section-head">
        <h2>Exports</h2>
        <span class="meta">secondary utility rail</span>
      </div>
      <div class="spotlight-grid">
        {''.join(exports_panel)}
      </div>
    </div>
    """
    page = html_document(
        SITE_DIR / "index.html",
        title="Gnars Camp",
        body=body,
        description="Analytics-first public site for Gnars DAO.",
    )
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
      <div class="eyebrow">Notes Index</div>
      <h1>Repository knowledge base rendered as a terminal vault.</h1>
      <p class="lede">Human-readable governance, operations, architecture, and archival context rendered from tracked markdown files.</p>
      <div class="command">ls notes/ && open note</div>
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
    for note in notes:
        list_items = []
        for item in notes:
            href = rel_href(note["output"], item["output"])
            list_items.append(f'<li><a href="{href}">{html.escape(item["title"])}</a></li>')
        properties_html = render_properties(note.get("properties", {}))
        body = f"""
        <div class="hero">
          <div class="eyebrow">Note</div>
          <h1>{html.escape(note['title'])}</h1>
          <p class="lede">{html.escape(note['summary'])}</p>
          <div class="command">cat {html.escape(note['relative_source'])}</div>
          <div class="meta path">{html.escape(note['relative_source'])}</div>
        </div>
        <div class="note-layout">
          <aside class="sidebar-stack">
            <section class="panel sidebar">
              <div class="section-head"><h2>Vault</h2></div>
              <ul>{''.join(list_items)}</ul>
            </section>
            <section class="panel">
              <div class="section-head"><h2>Properties</h2></div>
              {properties_html}
            </section>
          </aside>
          <article class="note">
            {note['html']}
          </article>
        </div>
        """
        page = html_document(note["output"], title=note["title"], body=body, description=note["summary"])
        write_text(note["output"], page)


def build_people_index(analytics: dict[str, Any]) -> None:
    overview = analytics["dao_metrics"]["overview"]
    cards = []
    for person in analytics["people"]["records"]:
        href = rel_href(people_index_path(), person_page_path(person["slug"]))
        filter_tags = "all " + " ".join(person["tags"])
        cards.append(
            f"""
            <article class="entity-card" data-filter-tags="{html.escape(filter_tags)}">
              <div class="kicker">{html.escape(person['address_short'])}</div>
              <h3><a href="{href}">{html.escape(person['display_name'])}</a></h3>
              <p class="muted">{html.escape(person['role'])}</p>
              <div class="pill-row">{join_pills(person['tags'][:5], muted=True)}</div>
              <div class="identity-meta">
                <span>{person['governance']['active_votes']} active votes</span>
                <span>{format_asset(person['receipts']['eth_received'], 'ETH')}</span>
                <span>{format_asset(person['receipts']['usdc_received'], 'USDC')}</span>
              </div>
            </article>
            """
        )

    body = f"""
    <div class="hero">
      <div class="eyebrow">People</div>
      <h1>Unified member, holder, delegate and contributor directory.</h1>
      <p class="lede">A single people surface built from the member snapshot, proposals archive, project ownership and payout recipients.</p>
      <div class="command">filter by holders / delegates / contributors / athletes / recipients / proposers</div>
    </div>

    <div class="metric-grid">
      <div class="metric-card"><strong>{overview['people_count']}</strong><span>profiles</span></div>
      <div class="metric-card"><strong>{overview['holders_count']}</strong><span>holders</span></div>
      <div class="metric-card"><strong>{overview['delegates_count']}</strong><span>delegates</span></div>
      <div class="metric-card"><strong>{overview['contributors_count']}</strong><span>contributors</span></div>
      <div class="metric-card"><strong>{overview['athletes_count']}</strong><span>athletes</span></div>
      <div class="metric-card"><strong>{overview['recipients_count']}</strong><span>recipients</span></div>
    </div>

    <div class="panel" style="margin-top: 24px;" data-filter-root data-default-filter="all">
      <div class="section-head">
        <h2>Directory</h2>
        <span class="meta">{overview['people_count']} public profiles</span>
      </div>
      <div class="filter-row" style="margin-bottom: 18px;">
        <button class="pill filter-chip" type="button" data-filter-value="all">All</button>
        <button class="pill filter-chip" type="button" data-filter-value="holder">Holders</button>
        <button class="pill filter-chip" type="button" data-filter-value="delegate">Delegates</button>
        <button class="pill filter-chip" type="button" data-filter-value="contributor">Contributors</button>
        <button class="pill filter-chip" type="button" data-filter-value="athlete">Athletes</button>
        <button class="pill filter-chip" type="button" data-filter-value="recipient">Recipients</button>
        <button class="pill filter-chip" type="button" data-filter-value="proposer">Proposers</button>
      </div>
      <div class="directory-grid">
        {''.join(cards)}
      </div>
    </div>
    """
    page = html_document(
        people_index_path(),
        title="Gnars People",
        body=body,
        description="Unified people directory for Gnars DAO.",
    )
    write_text(people_index_path(), page)


def build_people_pages(analytics: dict[str, Any]) -> None:
    updates_by_id = {record["update_id"]: record for record in analytics["project_updates"]["records"]}
    for person in analytics["people"]["records"]:
        payout_rows = [
            {
                "proposal": record["archive_id"],
                "asset": record["asset_symbol"],
                "amount": record["amount"],
                "project": record["project_id"] or "unassigned",
            }
            for record in analytics["spend_ledger"]["records"]
            if normalize_address(record["recipient_address"]) == normalize_address(person["address"])
        ][:12]

        authored_rows = []
        for archive_id in person["relationships"]["authored_proposals"][:12]:
            proposal = analytics["proposal_by_archive_id"].get(archive_id)
            if not proposal:
                continue
            authored_rows.append(
                {
                    "archive_id": archive_id,
                    "title": proposal_display_title(proposal),
                    "status": proposal["status"],
                    "end_at": proposal["end_at"],
                }
            )

        related_workstreams = []
        for project_id in person["relationships"]["related_projects"]:
            project = analytics["project_by_id"].get(project_id)
            if not project:
                continue
            href = rel_href(person_page_path(person["slug"]), workstream_page_path(project["slug"]))
            related_workstreams.append(
                f"""
                <div class="fact-row">
                  <a href="{href}"><strong>{html.escape(project['name'])}</strong></a>
                  <span>{format_asset(project['spent']['eth'], 'ETH')} / {format_asset(project['spent']['usdc'], 'USDC')}</span>
                </div>
                """
            )

        updates_markup = []
        for update_id in person["relationships"]["related_updates"]:
            update = updates_by_id.get(update_id)
            if not update:
                continue
            updates_markup.append(
                f"""
                <div class="timeline-item">
                  <span class="timeline-date">{html.escape(update['date'])} / {html.escape(update['status'])}</span>
                  <strong>{html.escape(update['title'])}</strong>
                  <span>{html.escape(update['summary'])}</span>
                </div>
                """
            )

        rank_rows = []
        for label, key in [
            ("ETH received", "eth_received"),
            ("USDC received", "usdc_received"),
            ("Active votes", "active_votes"),
            ("Proposals", "proposal_count"),
        ]:
            rows = analytics["dao_metrics"]["leaderboards"][key]
            for index, row in enumerate(rows, start=1):
                if normalize_address(row["address"]) != normalize_address(person["address"]):
                    continue
                rank_rows.append(
                    f'<div class="rank-row"><strong>{html.escape(label)}</strong><span class="rank-value">rank #{index} / {format_number(row["value"], 2 if key in {"eth_received", "usdc_received"} else 0)}</span></div>'
                )
                break

        body = f"""
        <div class="hero">
          <div class="eyebrow">Person</div>
          <h1>{html.escape(person['display_name'])}</h1>
          <p class="lede">{html.escape(person['bio'] or person['role'])}</p>
          <div class="command">{html.escape(person['address'])}</div>
          <div class="hero-rail">
            {join_pills(person['tags'][:6], muted=True)}
          </div>
        </div>

        <div class="metric-grid">
          <div class="metric-card"><strong>{person['governance']['holder_token_count']}</strong><span>held tokens</span></div>
          <div class="metric-card"><strong>{person['governance']['active_votes']}</strong><span>active votes</span></div>
          <div class="metric-card"><strong>{person['governance']['proposals_authored_count']}</strong><span>proposals authored</span></div>
          <div class="metric-card"><strong>{person['governance']['votes_cast_count']}</strong><span>votes cast</span></div>
          <div class="metric-card"><strong>{format_asset(person['receipts']['eth_received'], 'ETH')}</strong><span>ETH received</span></div>
          <div class="metric-card"><strong>{format_asset(person['receipts']['usdc_received'], 'USDC')}</strong><span>USDC received</span></div>
          <div class="metric-card"><strong>{format_asset(person['receipts']['gnars_received'], 'GNARS')}</strong><span>GNARS received</span></div>
          <div class="metric-card"><strong>{person['receipts']['nft_received_count']}</strong><span>NFTs received</span></div>
        </div>

        <div class="analytics-grid" style="margin-top: 24px;">
          <div class="section-stack">
            {table_panel("Direct receipts", ["proposal", "asset", "amount", "project"], payout_rows, "fungible transfers only")}
            {table_panel("Authored proposals", ["archive_id", "title", "status", "end_at"], authored_rows, "governance history")}
          </div>
          <div class="section-stack">
            <div class="panel">
              <div class="section-head"><h2>Identity</h2></div>
              <div class="identity-block">
                <div class="identity-meta">
                  <span>{html.escape(person['address'])}</span>
                  <span>attendance {format_pct(person['governance']['attendance_pct'])}</span>
                  <span>like {format_pct(person['governance']['like_pct'])}</span>
                </div>
                <div class="inline-links">
                  <a href="{html.escape(person['identity']['member_url'])}">member page</a>
                  {f'<a href="{html.escape(person["identity"]["farcaster"])}">farcaster</a>' if person['identity']['farcaster'] else ''}
                  {f'<a href="{html.escape(person["identity"]["github"])}">github</a>' if person['identity']['github'] else ''}
                </div>
                <p class="muted">{html.escape(person['notes'] or 'No editorial notes yet.')}</p>
              </div>
            </div>
            <div class="panel">
              <div class="section-head"><h2>Rankings</h2></div>
              <div class="rank-list">
                {''.join(rank_rows) or '<p class="muted">No leaderboard placement in the current top slices.</p>'}
              </div>
            </div>
          </div>
        </div>

        <div class="split" style="margin-top: 24px;">
          <div class="panel">
            <div class="section-head"><h2>Related workstreams</h2></div>
            <div class="facts">
              {''.join(related_workstreams) or '<p class="muted">No linked workstreams yet.</p>'}
            </div>
          </div>
          <div class="panel">
            <div class="section-head"><h2>Updates and milestones</h2></div>
            <div class="timeline-list">
              {''.join(updates_markup) or '<p class="muted">No manual updates linked yet.</p>'}
            </div>
          </div>
        </div>
        """
        page = html_document(
            person_page_path(person["slug"]),
            title=person["display_name"],
            body=body,
            description=f"Profile for {person['display_name']} in the Gnars people directory.",
        )
        write_text(person_page_path(person["slug"]), page)


def build_workstreams_index(analytics: dict[str, Any]) -> None:
    cards = []
    for project in analytics["project_rollups"]["records"]:
        href = rel_href(workstreams_index_path(), workstream_page_path(project["slug"]))
        cards.append(
            f"""
            <article class="entity-card">
              <div class="kicker">{html.escape(project['category'])}</div>
              <h3><a href="{href}">{html.escape(project['name'])}</a></h3>
              <p class="muted">{html.escape(project['objective'])}</p>
              <div class="identity-meta">
                <span>{html.escape(project['status'])}</span>
                <span>{format_asset(project['spent']['eth'], 'ETH')}</span>
                <span>{format_asset(project['spent']['usdc'], 'USDC')}</span>
                <span>{project['updates_count']} updates</span>
              </div>
            </article>
            """
        )

    body = f"""
    <div class="hero">
      <div class="eyebrow">Workstreams</div>
      <h1>Budget, spend, recipients and milestones by project.</h1>
      <p class="lede">Approved budgets from `projects.json` crossed with real fungible proposal payouts and editorial updates.</p>
      <div class="command">compare budget vs spent by asset, not synthetic USD</div>
    </div>
    <div class="workstream-grid">
      {''.join(cards)}
    </div>
    """
    page = html_document(
        workstreams_index_path(),
        title="Gnars Workstreams",
        body=body,
        description="Workstreams and budget utilization for Gnars DAO.",
    )
    write_text(workstreams_index_path(), page)


def build_workstream_pages(analytics: dict[str, Any]) -> None:
    updates_by_id = {record["update_id"]: record for record in analytics["project_updates"]["records"]}
    for project in analytics["project_rollups"]["records"]:
        recipient_rows = [
            {
                "recipient": record["display_name"],
                "eth": record["eth_received"],
                "usdc": record["usdc_received"],
                "gnars": record["gnars_received"],
                "nfts": record["nft_received_count"],
            }
            for record in project["recipients"]
        ]
        proposal_rows = [
            {
                "proposal_key": record["proposal_key"],
                "title": record["title"],
                "status": record["status"],
                "number": record["proposal_number"],
            }
            for record in project["proposal_summaries"]
        ]
        owner_links = []
        for address in project["owner_addresses"]:
            person = analytics["people_by_address"].get(normalize_address(address))
            if not person:
                owner_links.append(f"<span>{html.escape(short_address(address))}</span>")
                continue
            href = rel_href(workstream_page_path(project["slug"]), person_page_path(person["slug"]))
            owner_links.append(f'<a href="{href}">{html.escape(person["display_name"])}</a>')

        updates_markup = []
        for update_id in project["update_ids"]:
            update = updates_by_id.get(update_id)
            if not update:
                continue
            updates_markup.append(
                f"""
                <div class="timeline-item">
                  <span class="timeline-date">{html.escape(update['date'])} / {html.escape(update['kind'])}</span>
                  <strong>{html.escape(update['title'])}</strong>
                  <span>{html.escape(update['summary'])}</span>
                </div>
                """
            )

        body = f"""
        <div class="hero">
          <div class="eyebrow">Workstream</div>
          <h1>{html.escape(project['name'])}</h1>
          <p class="lede">{html.escape(project['objective'])}</p>
          <div class="hero-rail">{join_pills([project['status'], project['category']], muted=True)}</div>
        </div>

        <div class="metric-grid">
          <div class="metric-card"><strong>{format_asset(project['budget']['eth'], 'ETH')}</strong><span>approved budget</span></div>
          <div class="metric-card"><strong>{format_asset(project['budget']['usdc'], 'USDC')}</strong><span>approved budget</span></div>
          <div class="metric-card"><strong>{format_asset(project['spent']['eth'], 'ETH')}</strong><span>realized spend</span></div>
          <div class="metric-card"><strong>{format_asset(project['spent']['usdc'], 'USDC')}</strong><span>realized spend</span></div>
          <div class="metric-card"><strong>{format_pct(project['utilization_pct']['eth'])}</strong><span>ETH utilization</span></div>
          <div class="metric-card"><strong>{format_pct(project['utilization_pct']['usdc'])}</strong><span>USDC utilization</span></div>
          <div class="metric-card"><strong>{len(project['recipients'])}</strong><span>recipients</span></div>
          <div class="metric-card"><strong>{project['updates_count']}</strong><span>manual updates</span></div>
        </div>

        <div class="split" style="margin-top: 24px;">
          <div class="panel">
            <div class="section-head"><h2>Owners</h2></div>
            <div class="panel-list">{''.join(f'<div>{item}</div>' for item in owner_links) or '<p class="muted">No owners listed.</p>'}</div>
          </div>
          <div class="panel">
            <div class="section-head"><h2>Outputs and KPIs</h2></div>
            <div class="pill-row">{join_pills(project['outputs'], muted=True)}</div>
            <div class="pill-row" style="margin-top: 10px;">{join_pills(project['kpis'], muted=True)}</div>
          </div>
        </div>

        <div class="analytics-grid" style="margin-top: 24px;">
          <div class="section-stack">
            {table_panel("Recipients", ["recipient", "eth", "usdc", "gnars", "nfts"], recipient_rows, "per address")}
            {table_panel("Linked proposals", ["proposal_key", "title", "status", "number"], proposal_rows, "origin proposals")}
          </div>
          <div class="panel">
            <div class="section-head"><h2>Milestones and updates</h2></div>
            <div class="timeline-list">
              {''.join(updates_markup) or '<p class="muted">No updates recorded.</p>'}
            </div>
          </div>
        </div>
        """
        page = html_document(
            workstream_page_path(project["slug"]),
            title=project["name"],
            body=body,
            description=f"Workstream view for {project['name']}.",
        )
        write_text(workstream_page_path(project["slug"]), page)


def build_treasury_page(analytics: dict[str, Any]) -> None:
    metrics = analytics["dao_metrics"]
    treasury = analytics["treasury"]
    asset_rows = [
        {
            "symbol": record["symbol"],
            "name": record["name"],
            "amount": record["amount"],
            "value_usd": record["value_usd"],
        }
        for record in treasury["records"]
    ]
    recent_payout_rows = [
        {
            "proposal": record["archive_id"],
            "recipient": record["recipient_display_name"],
            "asset": record["asset_symbol"],
            "amount": record["amount"],
        }
        for record in analytics["dao_metrics"]["recent"]["payouts"][:12]
    ]
    top_recipient_rows = [
        {
            "person": record["display_name"],
            "amount": record["value"],
            "address": short_address(record["address"]),
        }
        for record in metrics["leaderboards"]["usdc_received"][:12]
    ]

    body = f"""
    <div class="hero">
      <div class="eyebrow">Treasury</div>
      <h1>Current holdings plus governance-approved outflows.</h1>
      <p class="lede">Treasury holdings come from the live Gnars treasury surface. Spend and recipients come only from decoded governance payouts, not from a full wallet accounting ledger.</p>
      <div class="command">{html.escape(treasury['wallet']['address'])}</div>
    </div>

    <div class="metric-grid">
      <div class="metric-card"><strong>${format_number(metrics['treasury']['treasury_page_total_value_usd'])}</strong><span>treasury holdings</span></div>
      <div class="metric-card"><strong>{format_asset(metrics['overview']['outflows_eth'], 'ETH')}</strong><span>decoded ETH outflows</span></div>
      <div class="metric-card"><strong>{format_asset(metrics['overview']['outflows_usdc'], 'USDC')}</strong><span>decoded USDC outflows</span></div>
      <div class="metric-card"><strong>{metrics['overview']['fungible_transfer_count']}</strong><span>fungible transfers</span></div>
      <div class="metric-card"><strong>{metrics['overview']['nft_transfer_count']}</strong><span>NFT transfers</span></div>
      <div class="metric-card"><strong>${format_number(metrics['treasury']['treasury_page_display_total_usd'])}</strong><span>visible treasury widget</span></div>
    </div>

    <div class="analytics-grid" style="margin-top: 24px;">
      <div class="section-stack">
        {table_panel("Holdings", ["symbol", "name", "amount", "value_usd"], asset_rows, "live treasury snapshot")}
        {table_panel("Recent payouts", ["proposal", "recipient", "asset", "amount"], recent_payout_rows, "approved governance transfers")}
      </div>
      <div class="section-stack">
        {table_panel("Top USDC recipients", ["person", "amount", "address"], top_recipient_rows, "current archive")}
      </div>
    </div>
    """
    page = html_document(
        treasury_page_path(),
        title="Gnars Treasury",
        body=body,
        description="Treasury holdings and governance-approved outflows.",
    )
    write_text(treasury_page_path(), page)


def build_proposals_index(analytics: dict[str, Any]) -> None:
    records = sorted(
        analytics["proposals_archive"]["records"],
        key=lambda record: (
            record.get("proposal_number") if record.get("proposal_number") is not None else -1,
            record.get("created_at") or "",
        ),
        reverse=True,
    )
    cards = []
    for proposal in records:
        href = rel_href(proposals_index_path(), proposal_page_path(proposal["archive_id"]))
        proposer = analytics["people_by_address"].get(normalize_address(proposal.get("proposer")))
        proposer_name = proposer["display_name"] if proposer else short_address(proposal.get("proposer"))
        cards.append(
            f"""
            <article class="entity-card">
              <div class="kicker">{html.escape(proposal['status'])}</div>
              <h3><a href="{href}">{html.escape(proposal_display_title(proposal))}</a></h3>
              <p class="muted">{html.escape(clamp_text(proposal['content_summary'], 180))}</p>
              <div class="identity-meta">
                <span>P{proposal['proposal_number'] if proposal.get('proposal_number') is not None else 'n/a'}</span>
                <span>{html.escape(proposer_name)}</span>
                <span>{len(proposal['votes'])} votes</span>
              </div>
            </article>
            """
        )

    body = f"""
    <div class="hero">
      <div class="eyebrow">Proposals</div>
      <h1>All archived proposals with linked people, workstreams and payout summaries.</h1>
      <p class="lede">The archive page turns every proposal into a navigable object in the DAO graph instead of just a download row.</p>
      <div class="command">proposal pages link back to people and workstreams</div>
    </div>
    <div class="proposal-grid">
      {''.join(cards)}
    </div>
    """
    page = html_document(
        proposals_index_path(),
        title="Gnars Proposals",
        body=body,
        description="Static proposal archive for Gnars DAO.",
    )
    write_text(proposals_index_path(), page)


def build_proposal_pages(analytics: dict[str, Any]) -> None:
    project_by_archive_id: dict[str, dict[str, Any]] = {}
    for project in analytics["project_rollups"]["records"]:
        for summary in project["proposal_summaries"]:
            if summary.get("archive_id"):
                project_by_archive_id[summary["archive_id"]] = project

    for proposal in analytics["proposals_archive"]["records"]:
        related_spend = [
            {
                "recipient": record["recipient_display_name"],
                "asset": record["asset_symbol"],
                "amount": record["amount"],
                "project": record["project_id"] or "unassigned",
            }
            for record in analytics["spend_ledger"]["records"]
            if record["archive_id"] == proposal["archive_id"]
        ]
        vote_rows = []
        for vote in sorted(
            proposal["votes"],
            key=lambda record: float(record.get("votes") or 0),
            reverse=True,
        )[:12]:
            voter = analytics["people_by_address"].get(normalize_address(vote.get("voter")))
            vote_rows.append(
                {
                    "voter": voter["display_name"] if voter else short_address(vote.get("voter")),
                    "votes": vote.get("votes"),
                    "choice": json.dumps(vote.get("choice"), ensure_ascii=False),
                }
            )

        proposer = analytics["people_by_address"].get(normalize_address(proposal.get("proposer")))
        proposer_markup = short_address(proposal.get("proposer"))
        if proposer:
            proposer_href = rel_href(proposal_page_path(proposal["archive_id"]), person_page_path(proposer["slug"]))
            proposer_markup = f'<a href="{proposer_href}">{html.escape(proposer["display_name"])}</a>'

        related_project = project_by_archive_id.get(proposal["archive_id"])
        related_project_markup = '<span class="muted">No linked workstream</span>'
        if related_project:
            project_href = rel_href(proposal_page_path(proposal["archive_id"]), workstream_page_path(related_project["slug"]))
            related_project_markup = f'<a href="{project_href}">{html.escape(related_project["name"])}</a>'

        body = f"""
        <div class="hero">
          <div class="eyebrow">Proposal</div>
          <h1>{html.escape(proposal_display_title(proposal))}</h1>
          <p class="lede">{html.escape(proposal['content_summary'])}</p>
          <div class="hero-rail">{join_pills([proposal['status'], proposal['chain'], f'P{proposal["proposal_number"]}' if proposal.get('proposal_number') is not None else proposal['platform']], muted=True)}</div>
        </div>

        <div class="metric-grid">
          <div class="metric-card"><strong>{len(proposal['votes'])}</strong><span>votes archived</span></div>
          <div class="metric-card"><strong>{len(proposal['transactions'])}</strong><span>decoded txs</span></div>
          <div class="metric-card"><strong>{format_number(proposal['scores_total'])}</strong><span>total score</span></div>
          <div class="metric-card"><strong>{format_number(proposal['quorum'])}</strong><span>quorum</span></div>
        </div>

        <div class="split" style="margin-top: 24px;">
          <div class="panel">
            <div class="section-head"><h2>Properties</h2></div>
            <div class="facts">
              <div class="fact-row"><strong>Proposer</strong><span>{proposer_markup}</span></div>
              <div class="fact-row"><strong>Workstream</strong><span>{related_project_markup}</span></div>
              <div class="fact-row"><strong>Created</strong><span>{html.escape(proposal['created_at'])}</span></div>
              <div class="fact-row"><strong>Start</strong><span>{html.escape(proposal['start_at'])}</span></div>
              <div class="fact-row"><strong>End</strong><span>{html.escape(proposal['end_at'])}</span></div>
            </div>
          </div>
          <div class="panel">
            <div class="section-head"><h2>Links</h2></div>
            <div class="panel-list">
              <div><a href="{html.escape(proposal['links']['source_url'])}">source url</a></div>
              <div><a href="{html.escape(proposal['links']['canonical_url'])}">canonical url</a></div>
              {f'<div><a href="{html.escape(proposal["links"]["discussion_url"])}">discussion url</a></div>' if proposal['links']['discussion_url'] else ''}
              {f'<div><a href="{html.escape(proposal["links"]["explorer_url"])}">explorer url</a></div>' if proposal['links']['explorer_url'] else ''}
            </div>
          </div>
        </div>

        <div class="analytics-grid" style="margin-top: 24px;">
          <div class="section-stack">
            {table_panel("Payout summary", ["recipient", "asset", "amount", "project"], related_spend, "fungible only")}
            {table_panel("Top votes", ["voter", "votes", "choice"], vote_rows, "top 12 by raw voting power")}
          </div>
          <div class="panel">
            <div class="section-head"><h2>Proposal body</h2></div>
            <article class="note">
              {render_markdown(proposal['content_markdown'])}
            </article>
          </div>
        </div>
        """
        page = html_document(
            proposal_page_path(proposal["archive_id"]),
            title=proposal_display_title(proposal),
            body=body,
            description=proposal["content_summary"],
        )
        write_text(proposal_page_path(proposal["archive_id"]), page)


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
          <div class="command">curl {html.escape(download_href)}</div>
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
          <div class="command">curl {html.escape(download_href)}</div>
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
      <h1>JSON and CSV publication layer in terminal form.</h1>
      <p class="lede">Browsable previews plus direct file URLs for machine downloads.</p>
      <div class="command">open datasets/ && fetch machine outputs</div>
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


def build_media_page(media_library: dict[str, Any]) -> None:
    category_sections = []
    media_page = media_index_path()
    assets_anchor = "#assets"
    photos_anchor = "#photos"
    videos_anchor = "#videos"

    for category in media_library["categories"]:
        cards = []
        for item in category["items"]:
            asset_href = rel_href(media_page, SITE_DIR / item["relative_source"])
            if item["kind"] == "image":
                preview = f'<img src="{asset_href}" alt="{html.escape(item["title"])}" loading="lazy" />'
            elif item["kind"] == "video":
                preview = f'<video src="{asset_href}" preload="metadata" controls muted playsinline></video>'
            else:
                preview = '<div class="media-placeholder">FILE</div>'

            cards.append(
                f"""
                <article class="media-card" data-kind="{html.escape(item['kind'])}">
                  <a class="media-thumb" href="{asset_href}">
                    {preview}
                  </a>
                  <div class="media-meta">
                    <span>{html.escape(category['slug'])}</span>
                    <span>{html.escape(item['kind'])}</span>
                  </div>
                  <h3>{html.escape(item['title'])}</h3>
                  <p class="muted">{html.escape(item['summary'])}</p>
                  <div class="links">
                    <a href="{asset_href}">Open file</a>
                  </div>
                </article>
                """
            )

        if not cards:
            cards.append(
                f"""
                <div class="media-empty">
                  <strong>No files yet in `{html.escape(category['slug'])}/`.</strong><br />
                  {html.escape(category['summary'])}
                </div>
                """
            )

        category_sections.append(
            f"""
            <section class="media-section panel" id="{html.escape(category['slug'])}">
              <div class="media-intro">
                <div>
                  <div class="eyebrow">{html.escape(category['title'])}</div>
                  <h2 style="margin: 12px 0 8px;">{html.escape(category['title'])}</h2>
                  <p class="muted">{html.escape(category['summary'])}</p>
                </div>
                <div class="media-meta">
                  <span>{category['count']} item{'s' if category['count'] != 1 else ''}</span>
                  <span>folder /media/{html.escape(category['slug'])}</span>
                </div>
              </div>
              <div class="media-grid">
                {''.join(cards)}
              </div>
            </section>
            """
        )

    body = f"""
    <div class="hero">
      <div class="eyebrow">Media Library</div>
      <h1>Image, brand, and video assets with a cc0-lib inspired library layer.</h1>
      <p class="lede">A visual surface for Gnars photos, videos, and brand assets. Keep the archive public, browsable, and ready for remixing without losing the terminal/data-vault feel.</p>
      <div class="command">open media/ && browse assets, stills, banners, and edits</div>
      <div class="links">
        <a class="button" href="{assets_anchor}">Assets</a>
        <a class="button secondary" href="{photos_anchor}">Photos</a>
        <a class="button secondary" href="{videos_anchor}">Videos</a>
      </div>
    </div>

    <div class="media-toolbar">
      <div class="media-marquee">
        <div class="media-marquee-track">
          <span><strong>cc0-lib direction</strong> searchable visual archive</span>
          <span><strong>gnars mode</strong> keep it public and remix-friendly</span>
          <span><strong>structure</strong> logos / banners / socials / event stills / edits</span>
        </div>
      </div>
      <div class="media-filterbar">
        <div class="media-filters">
          <a class="media-chip" data-tone="yellow" href="{assets_anchor}">Assets</a>
          <a class="media-chip" data-tone="blue" href="{photos_anchor}">Photos</a>
          <a class="media-chip" data-tone="red" href="{videos_anchor}">Videos</a>
        </div>
        <div class="media-actions">
          <a class="media-chip" href="{rel_href(media_page, SITE_DIR / 'notes' / 'media' / 'assets' / 'README' / 'index.html')}">Asset Guidelines</a>
        </div>
      </div>
    </div>

    <div class="media-layout">
      {''.join(category_sections)}
    </div>
    """
    page = html_document(
        media_page,
        title="Gnars Media Library",
        body=body,
        description="Published visual library for Gnars media assets.",
    )
    write_text(media_page, page)


def write_search_assets(notes: list[dict[str, Any]], media_library: dict[str, Any], analytics: dict[str, Any]) -> None:
    write_text(SITE_DIR / "assets" / "search.js", SEARCH_JS.strip() + "\n")
    write_text(
        SITE_DIR / "assets" / "search-index.json",
        json.dumps(build_search_index(notes, media_library, analytics), indent=2, ensure_ascii=False) + "\n",
    )


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
    media_library = discover_media_library()
    analytics = load_analytics()
    write_search_assets(notes, media_library, analytics)
    build_home(notes, media_library, analytics)
    build_people_index(analytics)
    build_people_pages(analytics)
    build_workstreams_index(analytics)
    build_workstream_pages(analytics)
    build_treasury_page(analytics)
    build_proposals_index(analytics)
    build_proposal_pages(analytics)
    build_notes_index(notes)
    build_note_pages(notes)
    build_dataset_pages()
    build_media_page(media_library)
    print(f"[ok] built {SITE_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
