import { rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const distDir = path.resolve(scriptDir, "..", "dist");

async function sleep(ms) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function removeDist(retries = 5) {
  for (let attempt = 1; attempt <= retries; attempt += 1) {
    try {
      await rm(distDir, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 });
      return;
    } catch (error) {
      if (attempt === retries) {
        throw error;
      }
      await sleep(250 * attempt);
    }
  }
}

await removeDist();
console.log("[ok] cleaned dist");
