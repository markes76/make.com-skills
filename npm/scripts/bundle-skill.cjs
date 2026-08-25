"use strict";

// Keep the npm bridge and AI skill in one versioned release. The generated
// bundle contains public guidance only; user-local learning is never copied.
const fs = require("node:fs");
const path = require("node:path");

const packageRoot = path.resolve(__dirname, "..");
const repositoryRoot = path.resolve(packageRoot, "..");
const target = path.join(packageRoot, "skill");
const entries = ["SKILL.md", "COMMUNITY_NOTICE.md", "references", "sources", "docs", "learning", "scripts/search_sources.py"];

if (!fs.existsSync(path.join(repositoryRoot, "SKILL.md"))) {
  if (fs.existsSync(path.join(target, "SKILL.md"))) {
    console.log("Bundled AI skill is already present.");
    process.exit(0);
  }
  throw new Error(`Could not find Make Skills source at ${repositoryRoot}.`);
}

fs.rmSync(target, { recursive: true, force: true });
fs.mkdirSync(target, { recursive: true });
for (const entry of entries) {
  const source = path.join(repositoryRoot, entry);
  if (!fs.existsSync(source)) throw new Error(`Required AI skill entry is missing: ${source}`);
  const destination = path.join(target, entry);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.cpSync(source, destination, {
    recursive: true,
    filter: (item) => !item.includes("__pycache__") && !item.endsWith(".pyc") && !item.endsWith("upstream-source-state.json"),
  });
}
console.log(`Bundled AI skill from ${repositoryRoot}.`);
