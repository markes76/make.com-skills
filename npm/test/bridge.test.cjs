"use strict";

const assert = require("node:assert/strict");
const { EventEmitter } = require("node:events");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  buildPythonEnvironment,
  buildPythonInvocation,
  commandFromArguments,
  detectPython,
  disableNotifications,
  enableNotifications,
  fetchLatestFromRegistry,
  isVersionNewer,
  isNotificationEligibleCommand,
  maybeShowUpdateNotification,
  notificationConfigPath,
  notificationLockPath,
  normalizePythonArguments,
  pythonCandidates,
  readNotificationPreference,
  updateMessage,
  withManagedMakeCli,
} = require("../lib/bridge.cjs");
const {
  installSkill,
  parseSkillArguments,
} = require("../lib/skill-installer.cjs");
const {
  extractVerifiedBinary,
  installOfficialCli,
  managedCliPath,
  selectOfficialCliArtifact,
  sha256,
} = require("../lib/official-cli-installer.cjs");

function tarGzipEntry(name, data) {
  const header = Buffer.alloc(512);
  header.write(name, 0, "utf8");
  header.write(`${data.length.toString(8).padStart(11, "0")}\0`, 124, "utf8");
  header[156] = "0".charCodeAt(0);
  const padding = Buffer.alloc((512 - (data.length % 512)) % 512);
  return require("node:zlib").gzipSync(Buffer.concat([header, data, padding, Buffer.alloc(1024)]));
}

test("detectPython prefers an explicit Python 3 interpreter", () => {
  const calls = [];
  const found = detectPython({
    platform: "darwin",
    env: { MAKE_SKILLS_PYTHON: "/opt/python3", PATH: "/usr/bin" },
    probe: (command, args) => {
      calls.push([command, args]);
      return { ok: command === "/opt/python3", version: "Python 3.12.4" };
    },
  });
  assert.deepEqual(found, {
    command: "/opt/python3",
    prefixArgs: [],
    source: "MAKE_SKILLS_PYTHON",
    version: "Python 3.12.4",
  });
  assert.deepEqual(calls, [["/opt/python3", ["--version"]]]);
});

test("detectPython uses the Windows py -3 launcher and rejects Python 2", () => {
  const found = detectPython({
    platform: "win32",
    env: {},
    probe: (command) => {
      if (command === "py") return { ok: true, version: "Python 3.11.9" };
      return { ok: true, version: "Python 2.7.18" };
    },
  });
  assert.equal(found.command, "py");
  assert.deepEqual(found.prefixArgs, ["-3"]);
  assert.equal(found.version, "Python 3.11.9");
  assert.deepEqual(pythonCandidates("win32", {}).slice(0, 3).map((item) => item.command), ["py", "python3", "python"]);
});

test("Python invocation isolates imports to the installed package while preserving the caller directory", () => {
  const packageRoot = path.join(path.sep, "opt", "node_modules", "make-com-skills");
  const invocation = buildPythonInvocation(
    { command: "python3", prefixArgs: [] },
    ["doctor", "--json", "--make-cli", "/safe/path/make-cli"],
    { packageRoot, env: { PYTHONPATH: "/existing", KEEP: "yes" } },
  );
  assert.equal(invocation.command, "python3");
  assert.equal(invocation.args[0], "-I");
  assert.equal(invocation.args[1], "-c");
  assert.match(invocation.args[2], /runpy\.run_module\('make_skills'/);
  assert.equal(invocation.args[3], path.join(packageRoot, "python"));
  assert.deepEqual(invocation.args.slice(4), ["--make-cli", "/safe/path/make-cli", "doctor", "--json"]);
  assert.equal(Object.hasOwn(invocation.env, "PYTHONPATH"), false);
  assert.equal(invocation.env.PYTHONDONTWRITEBYTECODE, "1");
  assert.equal(invocation.env.KEEP, "yes");
  assert.equal(Object.hasOwn(buildPythonEnvironment(packageRoot, {}), "PYTHONPATH"), false);
});

test("the bridge accepts --make-cli before or after a Python subcommand", () => {
  assert.deepEqual(normalizePythonArguments(["--make-cli", "/a/cli", "wizard"]), ["--make-cli", "/a/cli", "wizard"]);
  assert.deepEqual(normalizePythonArguments(["doctor", "--make-cli=/a/cli", "--json"]), ["--make-cli", "/a/cli", "doctor", "--json"]);
  assert.throws(() => normalizePythonArguments(["wizard", "--make-cli"]), /requires an executable path/);
});

test("only doctor and wizard are eligible for opt-in update notices", () => {
  assert.equal(isNotificationEligibleCommand(["doctor", "--json"]), true);
  assert.equal(isNotificationEligibleCommand(["--make-cli", "/a/cli", "wizard"]), true);
  assert.equal(isNotificationEligibleCommand(["review", "1905530", "--json"]), false);
});

test("command routing supports only safe bridge actions", () => {
  assert.deepEqual(commandFromArguments([]), { type: "onboarding" });
  assert.deepEqual(commandFromArguments(["--make-cli", "/safe/path/make-cli", "doctor"]), {
    type: "python",
    forwardedArgs: ["--make-cli", "/safe/path/make-cli", "doctor"],
  });
  assert.deepEqual(commandFromArguments(["wizard", "--make-cli", "/safe/path/make-cli"]), {
    type: "python",
    forwardedArgs: ["--make-cli", "/safe/path/make-cli", "wizard"],
  });
  assert.deepEqual(commandFromArguments(["update"]), { type: "update" });
  assert.deepEqual(commandFromArguments(["review", "1905530", "--json"]), {
    type: "python",
    forwardedArgs: ["review", "1905530", "--json"],
  });
  assert.deepEqual(commandFromArguments(["learn", "--consent", "--code", "GENERIC_CHECK", "--summary", "Use a live check.", "--recommendation", "Revalidate first."]), {
    type: "python",
    forwardedArgs: ["learn", "--consent", "--code", "GENERIC_CHECK", "--summary", "Use a live check.", "--recommendation", "Revalidate first."],
  });
  assert.deepEqual(commandFromArguments(["notifications", "enable"]), { type: "notifications", action: "enable" });
  assert.deepEqual(commandFromArguments(["make-cli", "status"]), { type: "make-cli", action: "status", assumeYes: false });
  assert.deepEqual(commandFromArguments(["make-cli", "install", "--yes"]), { type: "make-cli", action: "install", assumeYes: true });
  assert.throws(() => commandFromArguments(["update", "--yes"]), /does not accept/);
  assert.throws(() => commandFromArguments(["notifications", "maybe"]), /notifications/);
  assert.throws(() => commandFromArguments(["make-cli", "install", "--force"]), /make-cli/);
  assert.throws(() => commandFromArguments(["publish"]), /Unsupported command/);
});

test("AI skill installer copies only the packaged public skill after an explicit command", (t) => {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "make-com-skills-ai-skill-"));
  t.after(() => fs.rmSync(temporary, { recursive: true, force: true }));
  const packageRoot = path.join(temporary, "package");
  const template = path.join(packageRoot, "skill");
  fs.mkdirSync(path.join(template, "references"), { recursive: true });
  fs.writeFileSync(path.join(template, "SKILL.md"), "---\nname: make-automation-guru\ndescription: Test skill\n---\n");
  fs.writeFileSync(path.join(template, "references", "ai-engagement.md"), "test\n");
  const command = parseSkillArguments(["skill", "install", "--target", "codex"]);
  const messages = [];
  assert.equal(installSkill(command, { packageRoot, homeDirectory: path.join(temporary, "home"), write: (message) => messages.push(message) }), 0);
  const destination = path.join(temporary, "home", ".codex", "skills", "make-automation-guru");
  assert.equal(fs.existsSync(path.join(destination, "SKILL.md")), true);
  assert.equal(fs.existsSync(path.join(destination, "references", "ai-engagement.md")), true);
  assert.match(messages.join("\n"), /AI-first/);
  assert.throws(() => installSkill(command, { packageRoot, homeDirectory: path.join(temporary, "home") }), /Refusing to overwrite/);
});

test("the official CLI installer selects only supported verified artifacts", () => {
  const artifact = selectOfficialCliArtifact({ platform: "darwin", architecture: "arm64" });
  assert.equal(artifact.asset, "make-cli-darwin-arm64.tar.gz");
  assert.equal(artifact.binary, "make-cli-darwin-arm64");
  assert.match(artifact.sha256, /^[a-f0-9]{64}$/);
  assert.throws(() => selectOfficialCliArtifact({ platform: "freebsd", architecture: "x64" }), /No verified official Make CLI installer/);
});

test("the official CLI installer verifies archive bytes and extracts only the expected file", async (t) => {
  const data = Buffer.from("verified executable bytes");
  const archive = tarGzipEntry("make-cli-darwin-arm64", data);
  const artifact = {
    key: "darwin-arm64",
    version: "test",
    url: "https://github.com/integromat/make-cli/releases/download/vtest/make-cli-darwin-arm64.tar.gz",
    binary: "make-cli-darwin-arm64",
    sha256: sha256(archive),
  };
  assert.deepEqual(extractVerifiedBinary(archive, artifact), data);
  assert.throws(() => extractVerifiedBinary(tarGzipEntry("nested/make-cli-darwin-arm64", data), artifact), /exactly the expected executable/);

  let downloadWasCalled = false;
  const cancelled = await installOfficialCli({
    artifact,
    destination: path.join(os.tmpdir(), "make-com-skills-installer-cancelled", artifact.binary),
    confirm: async () => false,
    download: async () => {
      downloadWasCalled = true;
      return archive;
    },
  });
  assert.equal(cancelled.status, "cancelled");
  assert.equal(downloadWasCalled, false, "a declined installation must not download anything");

  const tools = fs.mkdtempSync(path.join(os.tmpdir(), "make-com-skills-official-cli-"));
  t.after(() => fs.rmSync(tools, { recursive: true, force: true }));
  const destination = path.join(tools, "vtest", artifact.binary);
  const result = await installOfficialCli({ artifact, destination, confirm: async () => true, download: async () => archive });
  assert.equal(result.status, "installed");
  assert.deepEqual(fs.readFileSync(destination), data);
  assert.equal((fs.statSync(destination).mode & 0o777), 0o700);
  const alreadyInstalled = await installOfficialCli({ artifact, destination, confirm: async () => true, download: async () => archive });
  assert.equal(alreadyInstalled.status, "already-installed");
});

test("a verified managed binary is used only when no explicit CLI override exists", (t) => {
  const homeDirectory = fs.mkdtempSync(path.join(os.tmpdir(), "make-com-skills-managed-cli-"));
  t.after(() => fs.rmSync(homeDirectory, { recursive: true, force: true }));
  const options = { env: {}, platform: "darwin", architecture: "arm64", homeDirectory };
  const destination = managedCliPath(options);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.writeFileSync(destination, "binary");
  assert.deepEqual(withManagedMakeCli(["doctor"], options), ["--make-cli", destination, "doctor"]);
  assert.deepEqual(withManagedMakeCli(["--make-cli", "/custom/make-cli", "doctor"], options), ["--make-cli", "/custom/make-cli", "doctor"]);
  assert.deepEqual(withManagedMakeCli(["doctor"], { ...options, env: { MAKE_SKILLS_MAKE_CLI: "/custom/make-cli" } }), ["doctor"]);
});

test("update messaging is opt-in and never claims an install occurred", () => {
  const message = updateMessage("make-com-skills", "0.0.0-development", "0.4.0");
  assert.match(message, /npm install --global make-com-skills@0.4.0/);
  assert.match(message, /npx --yes make-com-skills@0.4.0 skill install --target codex/);
  assert.match(message, /No installation was performed/);
  assert.equal(isVersionNewer("0.4.0", "0.0.0-development"), true);
  assert.equal(isVersionNewer("0.4.0", "0.4.0"), false);
});

test("update checks only the npm registry latest endpoint", async () => {
  let requestedUrl = "";
  let requestOptions = null;
  const fakeGet = (url, options, callback) => {
    requestedUrl = url;
    requestOptions = options;
    const request = new EventEmitter();
    request.setTimeout = () => {};
    request.destroy = (error) => request.emit("error", error);
    process.nextTick(() => {
      const response = new EventEmitter();
      response.statusCode = 200;
      response.setEncoding = () => {};
      response.resume = () => {};
      callback(response);
      response.emit("data", '{"version":"1.2.3"}');
      response.emit("end");
    });
    return request;
  };
  const result = await fetchLatestFromRegistry("make-com-skills", { get: fakeGet });
  assert.equal(requestedUrl, "https://registry.npmjs.org/make-com-skills/latest");
  assert.equal(requestOptions.headers.Accept, "application/json");
  assert.deepEqual(result, { statusCode: 200, version: "1.2.3" });
});

test("notification preference is absent until an explicit enable, and disable removes it", (t) => {
  const configDirectory = fs.mkdtempSync(path.join(os.tmpdir(), "make-com-skills-notifications-"));
  t.after(() => fs.rmSync(configDirectory, { recursive: true, force: true }));
  const options = {
    env: { MAKE_COM_SKILLS_CONFIG_DIR: configDirectory },
    now: Date.UTC(2026, 7, 25, 12, 0, 0),
  };
  const configPath = notificationConfigPath(options);
  assert.equal(fs.existsSync(configPath), false);
  assert.equal(readNotificationPreference(options).enabled, false);
  assert.equal(fs.existsSync(configPath), false, "status reads must not create a preference file");

  enableNotifications(options);
  assert.equal(fs.existsSync(configPath), true);
  assert.equal(readNotificationPreference(options).enabled, true);

  assert.deepEqual(disableNotifications(options), { configPath, removed: true });
  assert.equal(fs.existsSync(configPath), false);
});

test("enabled notifications check at most once per 24 hours and only show an opt-in command", async (t) => {
  const configDirectory = fs.mkdtempSync(path.join(os.tmpdir(), "make-com-skills-notifications-"));
  t.after(() => fs.rmSync(configDirectory, { recursive: true, force: true }));
  const initialTime = Date.UTC(2026, 7, 25, 12, 0, 0);
  const baseOptions = { env: { MAKE_COM_SKILLS_CONFIG_DIR: configDirectory }, now: initialTime };
  enableNotifications(baseOptions);
  let calls = 0;
  const notices = [];
  const check = (now) => maybeShowUpdateNotification(
    { name: "make-com-skills", version: "0.0.0-development" },
    {
      ...baseOptions,
      now,
      fetchLatest: async () => {
        calls += 1;
        return { statusCode: 200, version: "0.4.0" };
      },
      notice: (message) => notices.push(message),
    },
  );

  assert.deepEqual(await check(initialTime), { checked: true, notified: true });
  assert.deepEqual(await check(initialTime + 23 * 60 * 60 * 1000), { checked: false, notified: false });
  assert.equal(calls, 1);
  assert.equal(notices.length, 1);
  assert.equal(fs.existsSync(notificationLockPath(baseOptions)), false, "the temporary check lock is released");
  assert.match(notices[0], /npm install --global make-com-skills@0.4.0/);
  assert.doesNotMatch(notices[0], /npx --yes/);
  assert.match(notices[0], /No installation was performed/);

  assert.deepEqual(await check(initialTime + 24 * 60 * 60 * 1000), { checked: true, notified: true });
  assert.equal(calls, 2);
});
