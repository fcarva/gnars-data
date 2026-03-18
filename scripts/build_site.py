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
    notes_href = rel_href(path, SITE_DIR / "notes" / "index.html")
    datasets_href = rel_href(path, SITE_DIR / "datasets" / "index.html")
    media_href = rel_href(path, SITE_DIR / "media" / "index.html")
    proposals_href = rel_href(path, SITE_DIR / "exports" / "proposals.csv")
    tags_href = rel_href(path, SITE_DIR / "exports" / "proposal_tags.csv")
    treasury_href = rel_href(path, dataset_page_path("data", DATA_DIR / "treasury.json"))
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
            <input class="search-input" type="search" placeholder="search notes, datasets, tags..." data-search-input />
            <div class="search-results" data-search-results hidden></div>
          </div>
          <button class="micro theme-toggle" type="button" data-theme-toggle aria-pressed="false">Dark</button>
          <a class="micro" href="{proposals_href}">proposals.csv</a>
          <a class="micro" href="{tags_href}">pilot-30</a>
        </div>
      </div>
      <div class="tabbar">
        <div class="tabset">
          {tab(home_href, "ALL", "home")}
          {tab(notes_href, "NOTES", "notes")}
          {tab(datasets_href, "DATA", "datasets")}
          {tab(media_href, "MEDIA", "media")}
          {tab(proposals_href, "PROPS")}
          {tab(tags_href, "TAGS")}
          {tab(treasury_href, "TREASURY")}
        </div>
      </div>
      <div class="workspace">
        {body}
      </div>
      <div class="footer">
        <div class="subline">canonical dao archive / synced exports / public pages</div>
        <div>tracked in <code>gnars-data</code></div>
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


def build_search_index(notes: list[dict[str, Any]], media_library: dict[str, Any]) -> list[dict[str, str]]:
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

    return entries


def build_home(notes: list[dict[str, Any]], media_library: dict[str, Any]) -> None:
    archive = load_json("proposals_archive")
    treasury = load_json("treasury")
    members = load_json("members")
    contracts = load_json("contracts")
    proposal_tags = load_json("proposal_tags")

    proposal_count = len(archive["records"])
    vote_count = sum(len(record["votes"]) for record in archive["records"])
    tx_count = sum(len(record["transactions"]) for record in archive["records"])
    pilot_count = len(proposal_tags["records"])

    latest_rows = [
        {
            "archive_id": record["archive_id"],
            "platform": record["platform"],
            "proposal_number": record["proposal_number"],
            "title": proposal_display_title(record),
            "status": record["status"],
        }
        for record in archive["records"][:5]
    ]
    latest_headers = ["archive_id", "platform", "proposal_number", "title", "status"]
    latest_table = render_table(latest_headers, latest_rows)
    feed_rows = []
    for record in archive["records"][:6]:
        label = f"P{record['proposal_number']}" if record.get("proposal_number") is not None else record["platform"].upper()
        feed_rows.append(
            f"""
            <div class="feed-row">
              <div class="feed-time">{html.escape(label)}</div>
              <div class="feed-body">
                <strong>{html.escape(proposal_display_title(record))}</strong><br />
                <span class="muted">{html.escape(record['platform'])} / {html.escape(record['status'])} / {html.escape(record.get('end_at') or 'no end date')}</span>
              </div>
            </div>
            """
        )

    latest_note_cards = []
    for note in notes[:6]:
        href = rel_href(SITE_DIR / "index.html", note["output"])
        latest_note_cards.append(
            f"""
            <div class="dataset-card">
              <div class="eyebrow">{html.escape(note['relative_source'].split('/')[0])}</div>
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

    media_cards = []
    for category in media_library["categories"]:
        media_cards.append(
            f"""
            <div class="dataset-card">
              <div class="eyebrow">{html.escape(category['title'])}</div>
              <h3>{category['count']} item{'s' if category['count'] != 1 else ''}</h3>
              <p class="muted">{html.escape(category['summary'])}</p>
              <div class="links">
                <a href="{rel_href(SITE_DIR / 'index.html', media_index_path())}#{html.escape(category['slug'])}">Open section</a>
              </div>
            </div>
            """
        )

    body = f"""
    <div class="hero">
      <div class="eyebrow">Noun Terminal Mode</div>
      <h1>Gnars DAO data, notes, and exports in one terminal-style public base.</h1>
      <p class="lede">A public console for the Gnars archive: governance records, treasury state, contract registry, proposal tags, and direct machine-download endpoints.</p>
      <div class="command">curl https://fcarva.github.io/gnars-data/exports/proposals.csv</div>
      <div class="links">
        <a class="button" href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'exports' / 'proposals.csv')}">Download `proposals.csv`</a>
        <a class="button secondary" href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'notes' / 'index.html')}">Browse notes</a>
        <a class="button secondary" href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'datasets' / 'index.html')}">Browse datasets</a>
        <a class="button secondary" href="{rel_href(SITE_DIR / 'index.html', media_index_path())}">Browse media</a>
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

    <div class="split">
      <div class="panel">
        <div class="section-head">
          <h2>Latest proposals</h2>
          <span class="meta">source: data/proposals_archive.json</span>
        </div>
        {latest_table}
      </div>
      <div class="panel">
        <div class="section-head">
          <h2>Live feed</h2>
          <span class="meta">recent proposal lane</span>
        </div>
        <div class="feed">
          {''.join(feed_rows)}
        </div>
      </div>
    </div>

    <div class="panel" style="margin-top: 24px;">
      <div class="section-head">
        <h2>Publishing endpoints</h2>
        <span class="meta">direct file urls</span>
      </div>
      <div class="list-rows">
        <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'exports' / 'proposals.csv')}">/exports/proposals.csv</a></div>
        <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'exports' / 'proposals_archive.csv')}">/exports/proposals_archive.csv</a></div>
        <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'data' / 'proposals_archive.json')}">/data/proposals_archive.json</a></div>
        <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'data' / 'proposal_tags.json')}">/data/proposal_tags.json</a></div>
        <div><a href="{rel_href(SITE_DIR / 'index.html', SITE_DIR / 'exports' / 'treasury.csv')}">/exports/treasury.csv</a></div>
      </div>
    </div>

    <div class="panel" style="margin-top: 24px;">
      <div class="section-head">
        <h2>Recent notes</h2>
        <span class="meta">governance / operations / publishing / tagging</span>
      </div>
      <div class="grid cards">
        {''.join(latest_note_cards)}
      </div>
    </div>

    <div class="panel" style="margin-top: 24px;">
      <div class="section-head">
        <h2>Downloads</h2>
        <span class="meta">csv and json ready for fetch</span>
      </div>
      <div class="grid datasets">
        {''.join(exports_panel)}
      </div>
    </div>

    <div class="panel" style="margin-top: 24px;">
      <div class="section-head">
        <h2>Media Library</h2>
        <span class="meta">{media_library['total_count']} published asset{'s' if media_library['total_count'] != 1 else ''}</span>
      </div>
      <div class="grid cards">
        {''.join(media_cards)}
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


def write_search_assets(notes: list[dict[str, Any]], media_library: dict[str, Any]) -> None:
    write_text(SITE_DIR / "assets" / "search.js", SEARCH_JS.strip() + "\n")
    write_text(
        SITE_DIR / "assets" / "search-index.json",
        json.dumps(build_search_index(notes, media_library), indent=2, ensure_ascii=False) + "\n",
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
    write_search_assets(notes, media_library)
    build_home(notes, media_library)
    build_notes_index(notes)
    build_note_pages(notes)
    build_dataset_pages()
    build_media_page(media_library)
    print(f"[ok] built {SITE_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
