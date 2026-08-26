"use strict";

// This installer copies the public AI skill bundle. It never reads Make data,
// credentials, or personal-learning files, and it does not run during npm
// installation. The user must invoke `make-com-skills skill install`.

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const SKILL_NAME = "make-automation-guru";
const TARGETS = new Set(["codex", "claude", "cursor", "gemini", "copilot", "openclaw", "agents"]);

function defaultScope(target) {
  return ["codex", "claude", "openclaw"].includes(target) ? "user" : "project";
}

function parseSkillArguments(args) {
  if (!["status", "install"].includes(args[1])) {
    throw new Error("Usage: make-com-skills skill <status|install> [--target codex|claude|cursor|gemini|copilot|openclaw|agents] [--scope user|project] [--project PATH] [--force]");
  }
  const command = { type: "skill", action: args[1], target: "codex", scope: null, project: process.cwd(), force: false };
  for (let index = 2; index < args.length; index += 1) {
    const argument = args[index];
    if (argument === "--target" || argument === "--scope" || argument === "--project") {
      const value = args[index + 1];
      if (!value) throw new Error(`${argument} requires a value.`);
      if (argument === "--target") command.target = value;
      if (argument === "--scope") command.scope = value;
      if (argument === "--project") command.project = value;
      index += 1;
    } else if (argument === "--force" && command.action === "install") {
      command.force = true;
    } else {
      throw new Error(`Unsupported skill option: ${argument}`);
    }
  }
  if (!TARGETS.has(command.target)) throw new Error(`Unsupported AI target: ${command.target}`);
  command.scope = command.scope || defaultScope(command.target);
  if (!["user", "project"].includes(command.scope)) throw new Error("--scope must be user or project.");
  if (command.scope === "user" && ["cursor", "gemini", "copilot", "agents"].includes(command.target)) {
    throw new Error(`${command.target} supports project scope only.`);
  }
  return command;
}

function homeDirectory(options = {}) {
  return options.homeDirectory || os.homedir();
}

function installationPaths(command, options = {}) {
  const home = homeDirectory(options);
  const project = path.resolve(command.project);
  let destination;
  if (command.target === "codex") destination = command.scope === "user" ? path.join(home, ".codex", "skills", SKILL_NAME) : path.join(project, ".codex", "skills", SKILL_NAME);
  else if (command.target === "claude") destination = command.scope === "user" ? path.join(home, ".claude", "skills", SKILL_NAME) : path.join(project, ".claude", "skills", SKILL_NAME);
  else if (command.target === "openclaw") destination = command.scope === "user" ? path.join(home, ".openclaw", "skills", SKILL_NAME) : path.join(project, ".agents", "skills", SKILL_NAME);
  else destination = path.join(project, ".agents", "skills", SKILL_NAME);

  const adapters = [];
  if (command.target === "cursor") {
    adapters.push({
      path: path.join(project, ".cursor", "rules", "make-automation-guru.mdc"),
      content: "---\ndescription: Use Make Automation Guru for Make.com scenario design and operations.\nalwaysApply: false\n---\n\n@../../.agents/skills/make-automation-guru/SKILL.md\n",
    });
  } else if (command.target === "gemini") {
    adapters.push({ path: path.join(project, "GEMINI.md"), content: "# Make Automation Guru\n\n@./.agents/skills/make-automation-guru/SKILL.md\n" });
  } else if (command.target === "agents") {
    adapters.push({ path: path.join(project, "AGENTS.md"), content: "# Make Automation Guru\n\n@.agents/skills/make-automation-guru/SKILL.md\n" });
  } else if (command.target === "copilot") {
    adapters.push({ path: path.join(project, "AGENTS.md"), content: "# Make Automation Guru\n\n@.agents/skills/make-automation-guru/SKILL.md\n" });
    adapters.push({ path: path.join(project, ".github", "copilot-instructions.md"), content: "# Make Automation Guru\n\n@../AGENTS.md\n" });
  }
  return { destination, adapters };
}

function copyDirectory(source, destination) {
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.cpSync(source, destination, { recursive: true, dereference: false, errorOnExist: false, force: true });
}

function installSkill(command, options = {}) {
  const packageRoot = options.packageRoot || path.resolve(__dirname, "..");
  const source = path.join(packageRoot, "skill");
  const write = options.write || console.log;
  if (!fs.existsSync(path.join(source, "SKILL.md"))) throw new Error("The packaged AI skill is missing. Reinstall a released package.");
  const { destination, adapters } = installationPaths(command, options);
  if (fs.existsSync(destination) && !command.force) {
    throw new Error(`Refusing to overwrite existing skill: ${destination}. Review it and re-run with --force only if replacement is intended.`);
  }
  const existingAdapter = adapters.find((adapter) => fs.existsSync(adapter.path));
  if (existingAdapter && !command.force) {
    throw new Error(`Refusing to overwrite existing adapter: ${existingAdapter.path}. Merge it manually or re-run with --force only if replacement is intended.`);
  }
  if (fs.existsSync(destination)) fs.rmSync(destination, { recursive: true, force: true });
  copyDirectory(source, destination);
  for (const adapter of adapters) {
    fs.mkdirSync(path.dirname(adapter.path), { recursive: true });
    fs.writeFileSync(adapter.path, adapter.content, "utf8");
  }
  write(`Installed AI-first Make Automation Guru skill: ${destination}`);
  for (const adapter of adapters) write(`Installed ${command.target} adapter: ${adapter.path}`);
  write("Open or restart your AI client, then ask it to review, troubleshoot, build, or document a Make scenario. The AI—not a terminal menu—will lead the engagement.");
  return 0;
}

function skillStatus(command, options = {}) {
  const write = options.write || console.log;
  const { destination, adapters } = installationPaths(command, options);
  write(`AI skill: ${fs.existsSync(path.join(destination, "SKILL.md")) ? "installed" : "not installed"}\nLocation: ${destination}`);
  for (const adapter of adapters) write(`Adapter: ${fs.existsSync(adapter.path) ? "installed" : "not installed"}\nLocation: ${adapter.path}`);
  return 0;
}

module.exports = { SKILL_NAME, TARGETS, defaultScope, parseSkillArguments, installationPaths, installSkill, skillStatus };
