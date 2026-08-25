"use strict";

const childProcess = require("node:child_process");
const fs = require("node:fs");
const https = require("node:https");
const os = require("node:os");
const path = require("node:path");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const SUPPORTED_COMMANDS = new Set(["doctor", "wizard", "review", "update", "notifications"]);
const NOTIFICATION_CHECK_INTERVAL_MS = 24 * 60 * 60 * 1000;
const NOTIFICATION_LOCK_STALE_MS = 5 * 60 * 1000;

function readManifest(packageRoot = PACKAGE_ROOT) {
  const manifestPath = path.join(packageRoot, "package.json");
  return JSON.parse(fs.readFileSync(manifestPath, "utf8"));
}

function parseVersion(value) {
  const match = String(value || "").match(/^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$/);
  if (!match) {
    return null;
  }
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
    prerelease: match[4] || "",
  };
}

function isVersionNewer(latest, current) {
  const left = parseVersion(latest);
  const right = parseVersion(current);
  if (!left || !right) {
    return false;
  }
  for (const field of ["major", "minor", "patch"]) {
    if (left[field] !== right[field]) {
      return left[field] > right[field];
    }
  }
  // A stable release is newer than a prerelease with the same numeric version.
  return !left.prerelease && Boolean(right.prerelease);
}

function pythonCandidates(platform = process.platform, env = process.env) {
  const candidates = [];
  if (env.MAKE_SKILLS_PYTHON) {
    candidates.push({ command: env.MAKE_SKILLS_PYTHON, prefixArgs: [], source: "MAKE_SKILLS_PYTHON" });
  }
  if (platform === "win32") {
    candidates.push(
      { command: "py", prefixArgs: ["-3"], source: "Windows Python launcher" },
      { command: "python3", prefixArgs: [], source: "PATH" },
      { command: "python", prefixArgs: [], source: "PATH" },
    );
  } else {
    candidates.push(
      { command: "python3", prefixArgs: [], source: "PATH" },
      { command: "python", prefixArgs: [], source: "PATH" },
      { command: "/usr/bin/python3", prefixArgs: [], source: "system path" },
    );
  }
  const seen = new Set();
  return candidates.filter((candidate) => {
    const key = `${candidate.command}\u0000${candidate.prefixArgs.join("\u0000")}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function probePython(command, args) {
  try {
    const result = childProcess.spawnSync(command, args, {
      encoding: "utf8",
      shell: false,
      windowsHide: true,
    });
    const output = `${result.stdout || ""}\n${result.stderr || ""}`.trim();
    const match = output.match(/Python\s+(\d+(?:\.\d+){0,2})/i);
    return {
      ok: !result.error && result.status === 0 && Boolean(match) && output.includes("Python 3"),
      version: match ? `Python ${match[1]}` : output,
      error: result.error ? result.error.message : "",
    };
  } catch (error) {
    return { ok: false, version: "", error: error.message };
  }
}

function detectPython(options = {}) {
  const env = options.env || process.env;
  const candidates = pythonCandidates(options.platform || process.platform, env);
  const probe = options.probe || probePython;
  for (const candidate of candidates) {
    const result = probe(candidate.command, [...candidate.prefixArgs, "--version"]);
    if (result && result.ok && /^Python\s+3(?:\.|$)/i.test(result.version || "")) {
      return { ...candidate, version: result.version };
    }
  }
  return null;
}

function bundledPythonPath(packageRoot = PACKAGE_ROOT) {
  return path.join(packageRoot, "python");
}

function hasBundledPython(packageRoot = PACKAGE_ROOT) {
  return fs.existsSync(path.join(bundledPythonPath(packageRoot), "make_skills", "__main__.py"));
}

function notificationConfigDirectory(options = {}) {
  const env = options.env || process.env;
  if (env.MAKE_COM_SKILLS_CONFIG_DIR) {
    return path.resolve(env.MAKE_COM_SKILLS_CONFIG_DIR);
  }
  const homeDirectory = options.homeDirectory || os.homedir();
  if ((options.platform || process.platform) === "win32") {
    const appData = env.APPDATA || env.LOCALAPPDATA || path.join(homeDirectory, "AppData", "Roaming");
    return path.join(appData, "make-com-skills");
  }
  return path.join(env.XDG_CONFIG_HOME || path.join(homeDirectory, ".config"), "make-com-skills");
}

function notificationConfigPath(options = {}) {
  return path.join(notificationConfigDirectory(options), "notifications.json");
}

function notificationLockPath(options = {}) {
  return path.join(notificationConfigDirectory(options), "notifications.lock");
}

function currentTimestamp(options = {}) {
  const raw = options.now instanceof Date ? options.now.getTime() : options.now;
  const timestamp = raw === undefined ? Date.now() : Number(raw);
  return Number.isFinite(timestamp) ? timestamp : Date.now();
}

function readNotificationPreference(options = {}) {
  const configPath = notificationConfigPath(options);
  if (!fs.existsSync(configPath)) {
    return { enabled: false, configured: false, configPath, lastCheckedAt: null, enabledAt: null };
  }
  try {
    const value = JSON.parse(fs.readFileSync(configPath, "utf8"));
    if (!value || typeof value !== "object") {
      throw new Error("Preference is not an object.");
    }
    return {
      enabled: value.enabled === true,
      configured: true,
      configPath,
      lastCheckedAt: typeof value.last_checked_at === "string" ? value.last_checked_at : null,
      enabledAt: typeof value.enabled_at === "string" ? value.enabled_at : null,
      invalid: false,
    };
  } catch (_error) {
    // A malformed local preference is treated as disabled rather than being
    // replaced implicitly. The user can explicitly enable it again.
    return { enabled: false, configured: true, configPath, lastCheckedAt: null, enabledAt: null, invalid: true };
  }
}

function writeNotificationPreference(preference, options = {}) {
  const configPath = notificationConfigPath(options);
  fs.mkdirSync(path.dirname(configPath), { recursive: true });
  const value = {
    schema_version: 1,
    enabled: true,
    enabled_at: preference.enabledAt || new Date(currentTimestamp(options)).toISOString(),
    last_checked_at: preference.lastCheckedAt || null,
  };
  fs.writeFileSync(configPath, `${JSON.stringify(value, null, 2)}\n`, { encoding: "utf8", mode: 0o600 });
  return { ...value, configPath };
}

function enableNotifications(options = {}) {
  const current = readNotificationPreference(options);
  return writeNotificationPreference(
    {
      enabledAt: current.enabledAt || new Date(currentTimestamp(options)).toISOString(),
      lastCheckedAt: current.enabled ? current.lastCheckedAt : null,
    },
    options,
  );
}

function disableNotifications(options = {}) {
  const configPath = notificationConfigPath(options);
  if (fs.existsSync(configPath)) {
    fs.unlinkSync(configPath);
    return { configPath, removed: true };
  }
  return { configPath, removed: false };
}

function isNotificationCheckDue(preference, now = Date.now()) {
  if (!preference.enabled || !preference.lastCheckedAt) {
    return Boolean(preference.enabled);
  }
  const lastChecked = Date.parse(preference.lastCheckedAt);
  if (!Number.isFinite(lastChecked)) {
    return true;
  }
  // A clock that moves backward should not cause more frequent checks.
  return now >= lastChecked && now - lastChecked >= NOTIFICATION_CHECK_INTERVAL_MS;
}

function isNotificationEligibleCommand(forwardedArgs) {
  const { remainingArgs } = extractMakeCliArguments(forwardedArgs);
  return remainingArgs[0] === "doctor" || remainingArgs[0] === "wizard";
}

function markNotificationChecked(options = {}) {
  const current = readNotificationPreference(options);
  if (!current.enabled) {
    return false;
  }
  writeNotificationPreference(
    {
      enabledAt: current.enabledAt,
      lastCheckedAt: new Date(currentTimestamp(options)).toISOString(),
    },
    options,
  );
  return true;
}

function acquireNotificationCheckLock(options = {}) {
  const lockPath = notificationLockPath(options);
  const create = () => {
    const descriptor = fs.openSync(lockPath, "wx", 0o600);
    fs.writeFileSync(descriptor, `${process.pid}\n`, "utf8");
    fs.closeSync(descriptor);
    return lockPath;
  };
  try {
    return create();
  } catch (error) {
    if (error.code !== "EEXIST") {
      return null;
    }
  }
  try {
    const age = Date.now() - fs.statSync(lockPath).mtimeMs;
    if (age > NOTIFICATION_LOCK_STALE_MS) {
      fs.unlinkSync(lockPath);
      return create();
    }
  } catch (_error) {
    // Another process may have released the lock; its next invocation can check.
  }
  return null;
}

function releaseNotificationCheckLock(lockPath) {
  if (!lockPath) {
    return;
  }
  try {
    fs.unlinkSync(lockPath);
  } catch (_error) {
    // The optional notification must never affect doctor or wizard execution.
  }
}

const BUNDLED_MODULE_RUNNER = [
  "import runpy, sys",
  "bundle = sys.argv.pop(1)",
  "sys.path.insert(0, bundle)",
  "sys.argv[0] = 'make-skills'",
  "runpy.run_module('make_skills', run_name='__main__', alter_sys=True)",
].join("; ");

function buildPythonEnvironment(_packageRoot = PACKAGE_ROOT, env = process.env) {
  // Python's isolated mode ignores PYTHONPATH, but remove it as a defense in
  // depth measure and to make the intended import boundary unambiguous.
  const { PYTHONPATH: _pythonPath, ...isolatedEnvironment } = env;
  return {
    ...isolatedEnvironment,
    // Do not create bytecode files inside a globally installed npm package.
    PYTHONDONTWRITEBYTECODE: "1",
  };
}

function buildPythonInvocation(python, forwardedArgs, options = {}) {
  const packageRoot = options.packageRoot || PACKAGE_ROOT;
  return {
    command: python.command,
    // Keep the caller's CWD for local plans, but run Python in isolated mode
    // and insert only the installed bundle. That prevents a make_skills folder
    // in an arbitrary project from shadowing the released companion.
    args: [
      ...python.prefixArgs,
      "-I",
      "-c",
      BUNDLED_MODULE_RUNNER,
      bundledPythonPath(packageRoot),
      ...normalizePythonArguments(forwardedArgs),
    ],
    env: buildPythonEnvironment(packageRoot, options.env || process.env),
  };
}

function normalizePythonArguments(forwardedArgs) {
  // The Python CLI defines --make-cli as a global option. Let end users place
  // it naturally before or after doctor/wizard without changing its value.
  const { globalArgs, remainingArgs } = extractMakeCliArguments(forwardedArgs);
  return [...globalArgs, ...remainingArgs];
}

function extractMakeCliArguments(forwardedArgs) {
  const globalArgs = [];
  const remainingArgs = [];
  for (let index = 0; index < forwardedArgs.length; index += 1) {
    const argument = forwardedArgs[index];
    if (argument === "--make-cli") {
      const value = forwardedArgs[index + 1];
      if (!value) {
        throw new Error("--make-cli requires an executable path.");
      }
      globalArgs.push(argument, value);
      index += 1;
    } else if (argument.startsWith("--make-cli=")) {
      const value = argument.slice("--make-cli=".length);
      if (!value) {
        throw new Error("--make-cli requires an executable path.");
      }
      globalArgs.push("--make-cli", value);
    } else {
      remainingArgs.push(argument);
    }
  }
  return { globalArgs, remainingArgs };
}

function commandFromArguments(argv) {
  const { globalArgs, remainingArgs: args } = extractMakeCliArguments(argv);
  if (!args.length) {
    return { type: "python", forwardedArgs: [...globalArgs, "wizard"] };
  }
  if (args[0] === "--version" || args[0] === "version") {
    if (args.length !== 1 || globalArgs.length) {
      throw new Error("--version does not accept additional arguments.");
    }
    return { type: "version" };
  }
  if (args[0] === "--help" || args[0] === "-h" || args[0] === "help") {
    if (globalArgs.length) {
      throw new Error("help does not accept --make-cli.");
    }
    return { type: "help" };
  }
  if (!SUPPORTED_COMMANDS.has(args[0])) {
    throw new Error(`Unsupported command: ${args[0]}`);
  }
  if (args[0] === "update") {
    if (args.length !== 1 || globalArgs.length) {
      throw new Error("update does not accept additional arguments.");
    }
    return { type: "update" };
  }
  if (args[0] === "notifications") {
    if (globalArgs.length || args.length !== 2 || !["enable", "disable", "status"].includes(args[1])) {
      throw new Error("Usage: make-com-skills notifications <enable|disable|status>");
    }
    return { type: "notifications", action: args[1] };
  }
  return { type: "python", forwardedArgs: [...globalArgs, ...args] };
}

function usage() {
  return [
    "Usage: make-com-skills [--version|doctor|wizard|review|update] [command options]",
    "",
    "Commands:",
    "  doctor   Verify a bundled Python 3 companion and the official Make CLI (read-only).",
    "  wizard   Start the read-first Make Skills wizard (default).",
    "  review <scenario-id>  Create a read-only derived review (supports --json).",
    "  update   Check the npm registry and print an opt-in update command; never installs anything.",
    "  notifications <enable|disable|status>  Manage opt-in 24-hour update notices for doctor/wizard.",
    "",
    "Python discovery: MAKE_SKILLS_PYTHON, then platform Python 3 candidates.",
    "Official Make CLI selection: pass --make-cli PATH or set MAKE_SKILLS_MAKE_CLI.",
    "Unofficial community companion: review every command before approving any third-party effect.",
  ].join("\n");
}

function fetchLatestFromRegistry(packageName, options = {}) {
  const get = options.get || https.get;
  const timeoutMs = options.timeoutMs || 5000;
  const url = `https://registry.npmjs.org/${encodeURIComponent(packageName)}/latest`;
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (value) => {
      if (!settled) {
        settled = true;
        resolve(value);
      }
    };
    let request;
    try {
      request = get(url, { headers: { Accept: "application/json", "User-Agent": "make-com-skills-update-check" } }, (response) => {
        if (response.statusCode !== 200) {
          response.resume();
          finish({ statusCode: response.statusCode || 0, version: null });
          return;
        }
        let body = "";
        response.setEncoding("utf8");
        response.on("data", (chunk) => {
          body += chunk;
          if (body.length > 128 * 1024) {
            request.destroy(new Error("Registry response exceeded 128 KiB."));
          }
        });
        response.on("end", () => {
          try {
            const payload = JSON.parse(body);
            finish({ statusCode: 200, version: typeof payload.version === "string" ? payload.version : null });
          } catch (error) {
            reject(new Error("The npm registry returned invalid JSON."));
          }
        });
      });
      request.setTimeout(timeoutMs, () => request.destroy(new Error("Registry update check timed out.")));
      request.on("error", (error) => {
        if (!settled) {
          settled = true;
          reject(error);
        }
      });
    } catch (error) {
      reject(error);
    }
  });
}

function updateMessage(packageName, currentVersion, latestVersion, statusCode = 200) {
  if (!latestVersion) {
    const detail = statusCode === 404 ? "No public package metadata was found" : "No release version was returned";
    return [
      `${detail} for ${packageName}.`,
      "The package may not be published yet, or the registry may be unavailable.",
      "No installation was performed.",
    ].join("\n");
  }
  if (!isVersionNewer(latestVersion, currentVersion)) {
    return [`make-com-skills is up to date (${currentVersion}; registry: ${latestVersion}).`, "No installation was performed."].join("\n");
  }
  return [
    `Update available: ${currentVersion} -> ${latestVersion}.`,
    "Review the release notes, then opt in with one of these commands:",
    `  npm install --global ${packageName}@${latestVersion}`,
    `  npx --yes ${packageName}@${latestVersion} wizard`,
    "No installation was performed.",
  ].join("\n");
}

function notificationUpdateMessage(packageName, currentVersion, latestVersion) {
  if (!latestVersion || !isVersionNewer(latestVersion, currentVersion)) {
    return null;
  }
  return [
    `Make.com Skills update available: ${currentVersion} -> ${latestVersion}.`,
    "To install after reviewing release notes, opt in with:",
    `  npm install --global ${packageName}@${latestVersion}`,
    "No installation was performed.",
  ].join("\n");
}

async function maybeShowUpdateNotification(manifest, options = {}) {
  const preference = readNotificationPreference(options);
  const now = currentTimestamp(options);
  if (!isNotificationCheckDue(preference, now)) {
    return { checked: false, notified: false };
  }
  const lockPath = acquireNotificationCheckLock(options);
  if (!lockPath) {
    return { checked: false, notified: false };
  }
  // Record the attempt before the request so concurrent invocations and failed
  // network requests still respect the user's once-per-24-hour preference.
  try {
    if (!markNotificationChecked({ ...options, now })) {
      return { checked: false, notified: false };
    }
    const fetchLatest = options.fetchLatest || ((packageName) => fetchLatestFromRegistry(packageName, { timeoutMs: 2000 }));
    const latest = await fetchLatest(manifest.name);
    const message = notificationUpdateMessage(manifest.name, manifest.version, latest.version);
    if (message) {
      // stderr keeps doctor --json valid for scripting.
      (options.notice || console.error)(message);
      return { checked: true, notified: true };
    }
    return { checked: true, notified: false };
  } catch (_error) {
    // Notifications are optional and must never block a doctor or wizard run.
    return { checked: true, notified: false };
  } finally {
    releaseNotificationCheckLock(lockPath);
  }
}

function manageNotifications(action, options = {}) {
  const write = options.write || console.log;
  if (action === "enable") {
    const preference = enableNotifications(options);
    write(`Update notifications enabled. Doctor and wizard will check at most once every 24 hours.\nConfig: ${preference.configPath}`);
    return 0;
  }
  if (action === "disable") {
    const result = disableNotifications(options);
    write(`Update notifications disabled. ${result.removed ? "Removed preference file" : "No preference file existed"}.`);
    return 0;
  }
  const preference = readNotificationPreference(options);
  if (preference.enabled) {
    write(`Update notifications: enabled\nConfig: ${preference.configPath}\nLast registry check: ${preference.lastCheckedAt || "never"}`);
  } else if (preference.invalid) {
    write(`Update notifications: disabled (preference file is invalid)\nConfig: ${preference.configPath}`);
  } else {
    write(`Update notifications: disabled (not configured)\nConfig: ${preference.configPath}`);
  }
  return 0;
}

function runPython(python, forwardedArgs, options = {}) {
  const invocation = buildPythonInvocation(python, forwardedArgs, options);
  return new Promise((resolve) => {
    const child = childProcess.spawn(invocation.command, invocation.args, {
      cwd: options.cwd || process.cwd(),
      env: invocation.env,
      stdio: "inherit",
      shell: false,
      windowsHide: true,
    });
    child.on("error", (error) => {
      console.error(`Unable to start Python 3 (${invocation.command}): ${error.message}`);
      resolve(2);
    });
    child.on("exit", (code, signal) => {
      resolve(typeof code === "number" ? code : signal ? 1 : 0);
    });
  });
}

async function main(argv = process.argv.slice(2), options = {}) {
  const packageRoot = options.packageRoot || PACKAGE_ROOT;
  const write = options.write || console.log;
  let command;
  try {
    command = commandFromArguments(argv);
  } catch (error) {
    console.error(`${error.message}\n\n${usage()}`);
    return 2;
  }
  const manifest = readManifest(packageRoot);
  if (command.type === "help") {
    write(usage());
    return 0;
  }
  if (command.type === "version") {
    write(`make-com-skills npm wrapper ${manifest.version}`);
    return 0;
  }
  if (command.type === "update") {
    write(`Checking the npm registry for ${manifest.name} (read-only)...`);
    try {
      const latest = await (options.fetchLatest || fetchLatestFromRegistry)(manifest.name);
      write(updateMessage(manifest.name, manifest.version, latest.version, latest.statusCode));
      return 0;
    } catch (error) {
      write(`Could not check npm for updates: ${error.message}`);
      write("No installation was performed.");
      return 1;
    }
  }
  if (command.type === "notifications") {
    return manageNotifications(command.action, options);
  }
  if (!hasBundledPython(packageRoot)) {
    console.error("The bundled Python companion is missing. Install a released package, or run `npm run bundle-python` from a repository checkout before using this development wrapper.");
    return 2;
  }
  const python = detectPython({ env: options.env || process.env, platform: options.platform || process.platform, probe: options.probe });
  if (!python) {
    console.error("A usable Python 3 interpreter was not found. Install Python 3 or set MAKE_SKILLS_PYTHON to its executable path.");
    return 2;
  }
  if (isNotificationEligibleCommand(command.forwardedArgs)) {
    await maybeShowUpdateNotification(manifest, {
      env: options.env || process.env,
      platform: options.platform || process.platform,
      homeDirectory: options.homeDirectory,
      now: options.now,
      fetchLatest: options.fetchLatest,
      notice: options.notice,
    });
  }
  return runPython(python, command.forwardedArgs, { packageRoot, env: options.env || process.env, cwd: options.cwd });
}

module.exports = {
  PACKAGE_ROOT,
  buildPythonEnvironment,
  buildPythonInvocation,
  bundledPythonPath,
  commandFromArguments,
  detectPython,
  disableNotifications,
  enableNotifications,
  extractMakeCliArguments,
  fetchLatestFromRegistry,
  hasBundledPython,
  isVersionNewer,
  isNotificationCheckDue,
  isNotificationEligibleCommand,
  main,
  manageNotifications,
  markNotificationChecked,
  maybeShowUpdateNotification,
  notificationConfigDirectory,
  notificationConfigPath,
  notificationLockPath,
  notificationUpdateMessage,
  normalizePythonArguments,
  parseVersion,
  probePython,
  pythonCandidates,
  runPython,
  updateMessage,
  usage,
  readNotificationPreference,
  releaseNotificationCheckLock,
  writeNotificationPreference,
};
