"use strict";

// This script intentionally resolves every path from the npm package root.
// In a repository checkout, it refreshes from the current root src/make_skills
// tree before packing. In a released tarball that source is absent, so the
// already-bundled python/make_skills tree remains untouched.
const fs = require("node:fs");
const path = require("node:path");

const packageRoot = path.resolve(__dirname, "..");
const target = path.join(packageRoot, "python", "make_skills");
const marker = path.join(target, "__main__.py");
const source = path.resolve(packageRoot, "..", "src", "make_skills");

if (!fs.existsSync(path.join(source, "__main__.py"))) {
  if (fs.existsSync(marker)) {
    console.log("Bundled Python companion is already present.");
    process.exit(0);
  }
  throw new Error(`Could not find Make Skills Python source at ${source}.`);
}

// `target` is generated content confined to this package's python/ directory.
if (fs.existsSync(target)) {
  fs.rmSync(target, { recursive: true, force: true });
}
fs.mkdirSync(path.dirname(target), { recursive: true });
fs.cpSync(source, target, {
  recursive: true,
  filter: (entry) => !entry.includes("__pycache__") && !entry.endsWith(".pyc"),
});
console.log(`Bundled Python companion from ${source}.`);
