import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(webRoot, "..");
const dataDir = path.join(repoRoot, "data");
const docsDir = path.join(repoRoot, "docs");
const publicDataDir = path.join(webRoot, "public", "data");

function toPosix(value) {
  return value.split(path.sep).join("/");
}

function stripMarkdown(value) {
  return value
    .replace(/!\[[^\]]*]\([^)]*\)/g, "")
    .replace(/\[[^\]]*]\(([^)]*)\)/g, "$1")
    .replace(/[`*_>#-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

async function walkMarkdown(directory) {
  const entries = await fs.readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await walkMarkdown(fullPath)));
    } else if (entry.isFile() && entry.name.endsWith(".md")) {
      files.push(fullPath);
    }
  }
  return files;
}

function headingFromContent(content, fallback) {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : fallback;
}

function excerptFromContent(content) {
  const cleaned = stripMarkdown(content).replace(
    /\b(?:csv|json|curl|download(?:able)?|exports?|datasets?)\b/gi,
    "",
  );
  return cleaned.length > 220 ? `${cleaned.slice(0, 217)}...` : cleaned;
}

async function buildNotesIndex() {
  const markdownFiles = await walkMarkdown(docsDir);
  markdownFiles.push(path.join(repoRoot, "README.md"));
  const records = [];
  for (const filePath of markdownFiles) {
    const relative = path.relative(repoRoot, filePath);
    const content = await fs.readFile(filePath, "utf8");
    const title = headingFromContent(content, path.basename(filePath, ".md"));
    const slug = toPosix(relative).replace(/[/.]+/g, "-").toLowerCase();
    const section = relative === "README.md" ? "root" : relative.split(path.sep)[0];
    records.push({
      slug,
      title,
      section,
      href: `/notes/#${slug}`,
      excerpt: excerptFromContent(content),
    });
  }
  records.sort((left, right) => left.title.localeCompare(right.title));
  return {
    dataset: "notes_index",
    as_of: new Date().toISOString(),
    version: 1,
    records,
  };
}

async function buildSearchIndex(notesIndex) {
  const readJson = async (filename) =>
    JSON.parse(await fs.readFile(path.join(dataDir, filename), "utf8"));

  const people = await readJson("people.json");
  const projects = await readJson("project_rollups.json");
  const proposals = await readJson("proposals_archive.json");
  const timeline = await readJson("timeline_events.json");

  const records = [];

  for (const person of people.records) {
    records.push({
      title: person.display_name,
      href: `/community/${person.slug}/`,
      kind: "Community",
      summary: stripMarkdown(person.bio || person.role || person.address_short),
    });
  }

  for (const project of projects.records) {
    records.push({
      title: project.name,
      href: `/projects/${project.project_id}/`,
      kind: "Project",
      summary: stripMarkdown(project.objective),
    });
  }

  for (const proposal of proposals.records) {
    const numberLabel = proposal.proposal_number !== null ? `Prop #${proposal.proposal_number}` : proposal.archive_id;
    records.push({
      title: `${numberLabel} - ${proposal.title}`,
      href: `/proposals/${proposal.archive_id}/`,
      kind: "Proposal",
      summary: stripMarkdown(proposal.content_summary),
    });
  }

  for (const event of timeline.records.slice(0, 240)) {
    records.push({
      title: event.title,
      href: event.archive_id ? `/proposals/${event.archive_id}/` : event.project_id ? `/projects/${event.project_id}/` : "/timeline/",
      kind: "Timeline",
      summary: stripMarkdown(event.summary),
    });
  }

  for (const note of notesIndex.records) {
    records.push({
      title: note.title,
      href: note.href,
      kind: "Archive",
      summary: note.excerpt,
    });
  }

  return {
    dataset: "search_index",
    as_of: new Date().toISOString(),
    version: 1,
    records,
  };
}

async function main() {
  await fs.rm(publicDataDir, { recursive: true, force: true });
  await fs.mkdir(publicDataDir, { recursive: true });

  const entries = await fs.readdir(dataDir, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isFile() || !entry.name.endsWith(".json")) {
      continue;
    }
    await fs.copyFile(path.join(dataDir, entry.name), path.join(publicDataDir, entry.name));
  }

  const notesIndex = await buildNotesIndex();
  await fs.writeFile(path.join(publicDataDir, "notes_index.json"), JSON.stringify(notesIndex, null, 2));

  const searchIndex = await buildSearchIndex(notesIndex);
  await fs.writeFile(path.join(publicDataDir, "search-index.json"), JSON.stringify(searchIndex, null, 2));

  console.log("[ok] prepared public data payloads");
}

await main();
