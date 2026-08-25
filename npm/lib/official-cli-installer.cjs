"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const https = require("node:https");
const os = require("node:os");
const path = require("node:path");
const readline = require("node:readline/promises");
const zlib = require("node:zlib");

const OFFICIAL_CLI_VERSION = "1.4.0";
const OFFICIAL_CLI_RELEASE_PAGE = `https://github.com/integromat/make-cli/releases/tag/v${OFFICIAL_CLI_VERSION}`;
const OFFICIAL_CLI_RELEASE_BASE = `https://github.com/integromat/make-cli/releases/download/v${OFFICIAL_CLI_VERSION}`;
const MAX_ARCHIVE_BYTES = 128 * 1024 * 1024;
const ALLOWED_DOWNLOAD_HOSTS = new Set(["github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"]);

const ARTIFACTS = Object.freeze({
  "darwin-amd64": Object.freeze({
    asset: "make-cli-darwin-amd64.tar.gz",
    binary: "make-cli-darwin-amd64",
    sha256: "8a9bb29fc7efae38f2ce70b4abbbb6cf293244faba445c9810f1f9cffb1cc1bd",
  }),
  "darwin-arm64": Object.freeze({
    asset: "make-cli-darwin-arm64.tar.gz",
    binary: "make-cli-darwin-arm64",
    sha256: "fd0316807f73c3640a89d747dd3b8e022fd651562a829c9f958ec469201bf742",
  }),
  "linux-amd64": Object.freeze({
    asset: "make-cli-linux-amd64.tar.gz",
    binary: "make-cli-linux-amd64",
    sha256: "ca0ef36dffdb3afd94bbdd85b6a24ab70d9a5d8705a1955b1b1603e4cca9a9bd",
  }),
  "linux-arm64": Object.freeze({
    asset: "make-cli-linux-arm64.tar.gz",
    binary: "make-cli-linux-arm64",
    sha256: "f6e5030df6a069278868cdfc8e43c6730ddf11d1f8d3babf5095175808bfabcf",
  }),
  "win32-amd64": Object.freeze({
    asset: "make-cli-windows-amd64.tar.gz",
    binary: "make-cli-windows-amd64.exe",
    sha256: "619d8b90776a6e0eff91cb8416fb2f0eb07838582f72223343a84fa835632f5a",
  }),
});

function platformKey(platform = process.platform, architecture = process.arch) {
  const platformName = { darwin: "darwin", linux: "linux", win32: "win32" }[platform];
  const architectureName = { x64: "amd64", arm64: "arm64" }[architecture];
  return platformName && architectureName ? `${platformName}-${architectureName}` : null;
}

function selectOfficialCliArtifact(options = {}) {
  const key = platformKey(options.platform || process.platform, options.architecture || process.arch);
  const artifact = key ? ARTIFACTS[key] : null;
  if (!artifact) {
    throw new Error(
      `No verified official Make CLI installer is available for ${options.platform || process.platform}/${options.architecture || process.arch}. ` +
        `Install it from ${OFFICIAL_CLI_RELEASE_PAGE}.`,
    );
  }
  return { ...artifact, key, version: OFFICIAL_CLI_VERSION, url: `${OFFICIAL_CLI_RELEASE_BASE}/${artifact.asset}` };
}

function toolsDirectory(options = {}) {
  const env = options.env || process.env;
  const homeDirectory = options.homeDirectory || os.homedir();
  if (env.MAKE_COM_SKILLS_TOOLS_DIR) {
    return path.resolve(env.MAKE_COM_SKILLS_TOOLS_DIR);
  }
  if ((options.platform || process.platform) === "win32") {
    return path.join(env.LOCALAPPDATA || env.APPDATA || path.join(homeDirectory, "AppData", "Local"), "make-com-skills", "tools", "make-cli");
  }
  return path.join(env.XDG_DATA_HOME || path.join(homeDirectory, ".local", "share"), "make-com-skills", "tools", "make-cli");
}

function managedCliPath(options = {}) {
  const artifact = options.artifact || selectOfficialCliArtifact(options);
  return path.join(toolsDirectory(options), `v${artifact.version || OFFICIAL_CLI_VERSION}`, artifact.binary);
}

function sha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function assertAllowedDownloadUrl(value) {
  const parsed = new URL(value);
  if (parsed.protocol !== "https:" || !ALLOWED_DOWNLOAD_HOSTS.has(parsed.hostname)) {
    throw new Error(`Refusing to download the official Make CLI from an untrusted URL: ${parsed.origin}`);
  }
  return parsed;
}

function downloadBuffer(url, options = {}, redirectCount = 0) {
  if (redirectCount > 3) {
    return Promise.reject(new Error("Official Make CLI download exceeded the redirect limit."));
  }
  const parsed = assertAllowedDownloadUrl(url);
  const get = options.get || https.get;
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (callback, value) => {
      if (!settled) {
        settled = true;
        callback(value);
      }
    };
    let request;
    try {
      request = get(parsed, { headers: { Accept: "application/octet-stream", "User-Agent": "make-com-skills-official-cli-installer" } }, (response) => {
        const status = response.statusCode || 0;
        if (status >= 300 && status < 400 && response.headers.location) {
          response.resume();
          const nextUrl = new URL(response.headers.location, parsed).toString();
          downloadBuffer(nextUrl, options, redirectCount + 1).then((value) => finish(resolve, value), (error) => finish(reject, error));
          return;
        }
        if (status !== 200) {
          response.resume();
          finish(reject, new Error(`Official Make CLI download returned HTTP ${status}.`));
          return;
        }
        const chunks = [];
        let total = 0;
        response.on("data", (chunk) => {
          total += chunk.length;
          if (total > MAX_ARCHIVE_BYTES) {
            request.destroy(new Error("Official Make CLI archive exceeded the allowed size."));
            return;
          }
          chunks.push(chunk);
        });
        response.on("end", () => finish(resolve, Buffer.concat(chunks)));
        response.on("error", (error) => finish(reject, error));
      });
      request.setTimeout(30000, () => request.destroy(new Error("Official Make CLI download timed out.")));
      request.on("error", (error) => finish(reject, error));
    } catch (error) {
      finish(reject, error);
    }
  });
}

function readTarString(header, offset, length) {
  const value = header.subarray(offset, offset + length);
  const terminator = value.indexOf(0);
  return value.subarray(0, terminator === -1 ? value.length : terminator).toString("utf8");
}

function readTarSize(header) {
  const raw = readTarString(header, 124, 12).trim();
  if (!raw) {
    return 0;
  }
  if (!/^[0-7]+$/.test(raw)) {
    throw new Error("Official Make CLI archive contains an invalid tar size.");
  }
  return Number.parseInt(raw, 8);
}

function tarEntries(tarball) {
  const entries = [];
  for (let offset = 0; offset + 512 <= tarball.length; ) {
    const header = tarball.subarray(offset, offset + 512);
    if (header.every((byte) => byte === 0)) {
      break;
    }
    const size = readTarSize(header);
    const name = readTarString(header, 0, 100);
    const prefix = readTarString(header, 345, 155);
    const entryName = prefix ? `${prefix}/${name}` : name;
    const type = String.fromCharCode(header[156] || 0);
    const contentOffset = offset + 512;
    const contentEnd = contentOffset + size;
    if (!entryName || contentEnd > tarball.length) {
      throw new Error("Official Make CLI archive is malformed.");
    }
    entries.push({ name: entryName, type, data: tarball.subarray(contentOffset, contentEnd) });
    offset = contentOffset + Math.ceil(size / 512) * 512;
  }
  return entries;
}

function extractVerifiedBinary(archive, artifact) {
  let tarball;
  try {
    tarball = zlib.gunzipSync(archive);
  } catch (_error) {
    throw new Error("Official Make CLI archive is not a valid gzip file.");
  }
  if (tarball.length > MAX_ARCHIVE_BYTES) {
    throw new Error("Official Make CLI archive expanded beyond the allowed size.");
  }
  const entries = tarEntries(tarball).filter((entry) => entry.name === artifact.binary && (entry.type === "0" || entry.type === "\0"));
  if (entries.length !== 1 || !entries[0].data.length) {
    throw new Error("Official Make CLI archive did not contain exactly the expected executable.");
  }
  return Buffer.from(entries[0].data);
}

function installSummary(artifact, destination) {
  return [
    `Official Make CLI v${artifact.version} (${artifact.key})`,
    `Source: ${artifact.url}`,
    `SHA-256: ${artifact.sha256}`,
    `Destination: ${destination}`,
  ].join("\n");
}

async function confirmInstall(summary, options = {}) {
  if (options.assumeYes) {
    return true;
  }
  if (options.confirm) {
    return Boolean(await options.confirm(summary));
  }
  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    throw new Error("Refusing a non-interactive download. Re-run `make-com-skills make-cli install --yes` after reviewing the source and checksum.");
  }
  const prompt = readline.createInterface({ input: process.stdin, output: process.stdout });
  try {
    const response = await prompt.question(`${summary}\nDownload and install this official Make CLI? [y/N] `);
    return /^(y|yes)$/i.test(response.trim());
  } finally {
    prompt.close();
  }
}

async function installOfficialCli(options = {}) {
  const artifact = options.artifact || selectOfficialCliArtifact(options);
  const destination = options.destination || managedCliPath({ ...options, artifact });
  if (fs.existsSync(destination)) {
    return { artifact, destination, status: "already-installed" };
  }
  const summary = installSummary(artifact, destination);
  if (!(await confirmInstall(summary, options))) {
    return { artifact, destination, status: "cancelled" };
  }
  const archive = await (options.download || downloadBuffer)(artifact.url, options);
  if (!Buffer.isBuffer(archive)) {
    throw new Error("Official Make CLI download did not return binary data.");
  }
  const actualHash = sha256(archive);
  if (actualHash !== artifact.sha256) {
    throw new Error(`Official Make CLI checksum mismatch. Expected ${artifact.sha256}, received ${actualHash}.`);
  }
  const binary = extractVerifiedBinary(archive, artifact);
  fs.mkdirSync(path.dirname(destination), { recursive: true, mode: 0o700 });
  const temporary = path.join(path.dirname(destination), `.${path.basename(destination)}.${process.pid}.tmp`);
  try {
    fs.writeFileSync(temporary, binary, { encoding: undefined, mode: 0o700, flag: "wx" });
    fs.chmodSync(temporary, 0o700);
    // link() fails if another local process created the destination after the
    // initial existence check, unlike rename() which can replace it on Unix.
    fs.linkSync(temporary, destination);
    fs.unlinkSync(temporary);
  } finally {
    if (fs.existsSync(temporary)) {
      fs.unlinkSync(temporary);
    }
  }
  return { artifact, destination, status: "installed" };
}

function managedCliStatus(options = {}) {
  const artifact = options.artifact || selectOfficialCliArtifact(options);
  const destination = options.destination || managedCliPath({ ...options, artifact });
  return { artifact, destination, installed: fs.existsSync(destination) };
}

module.exports = {
  ALLOWED_DOWNLOAD_HOSTS,
  ARTIFACTS,
  MAX_ARCHIVE_BYTES,
  OFFICIAL_CLI_RELEASE_PAGE,
  OFFICIAL_CLI_VERSION,
  assertAllowedDownloadUrl,
  downloadBuffer,
  extractVerifiedBinary,
  installOfficialCli,
  installSummary,
  managedCliPath,
  managedCliStatus,
  platformKey,
  selectOfficialCliArtifact,
  sha256,
  tarEntries,
  toolsDirectory,
};
