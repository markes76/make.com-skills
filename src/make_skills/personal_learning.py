"""Consent-gated, user-local learning memory for the Make Skills companion."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SECRET_PATTERNS = (
    re.compile(r"\b(?:ghp|github_pat|sk|xox[baprs]|AIza)[_-][A-Za-z0-9_-]{8,}\b", re.I),
    re.compile(r"(?im)\b(authorization|api[_ -]?key|token|password|secret)\s*[:=]\s*[^\r\n]+"),
)
URL_QUERY = re.compile(r"https?://[^\s?]+\?[^\s]+", re.I)
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
WEBHOOK_URL = re.compile(r"https?://[^\s]*(?:webhook|hooks)[^\s]*", re.I)


def default_directory() -> Path:
    """Return an overrideable user-local directory, never a repository path."""
    return Path(os.environ.get("MAKE_SKILLS_PERSONAL_DIR", "~/.make-com-skills")).expanduser()


def default_artifact_directory(kind: str) -> Path:
    """Keep potentially sensitive local outputs outside a cloned repository."""
    return default_directory() / kind


def ensure_private_directory(directory: Path) -> Path:
    """Create a user-local directory with restrictive permissions where supported."""
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        directory.chmod(0o700)
    except OSError:
        # Windows and managed filesystems can reject POSIX permission changes.
        pass
    return directory


def write_private_text(path: Path, value: str) -> Path:
    """Write a local artifact with owner-only permissions where supported."""
    ensure_private_directory(path.parent)
    path.write_text(value, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def sanitize(value: str, limit: int = 1_000) -> str:
    """Remove common secrets and personal identifiers before local retention."""
    value = WEBHOOK_URL.sub("[REDACTED_WEBHOOK_URL]", value)
    value = URL_QUERY.sub("[REDACTED_URL_QUERY]", value)
    value = EMAIL.sub("[REDACTED_EMAIL]", value)
    for pattern in SECRET_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value.strip()[:limit]


class PersonalLearningStore:
    """Store only generalized findings and user-verified lessons outside Git."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or default_directory()
        self.candidates_path = self.directory / "candidates.jsonl"
        self.verified_path = self.directory / "verified-lessons.jsonl"
        self.memory_path = self.directory / "memory.json"
        self.skill_path = self.directory / "PERSONAL_SKILL.md"

    def record_review(self, review: dict[str, Any]) -> str:
        """Continuously retain a sanitized, non-authoritative review candidate."""
        findings = self._findings(review)
        record = self._record("candidate", findings, verified=False)
        self._append(self.candidates_path, record)
        self._update_memory(findings, verified=False)
        self._render_personal_skill()
        return record["id"]

    def record_verified_resolution(self, review: dict[str, Any], verification: str | None = None) -> str:
        """Promote generalized findings after confirmation without retaining user prose."""
        findings = self._findings(review)
        record = self._record("verified", findings, verified=True)
        self._append(self.verified_path, record)
        self._update_memory(findings, verified=True)
        self._render_personal_skill()
        return record["id"]

    def _findings(self, review: dict[str, Any]) -> list[dict[str, str]]:
        raw = review.get("findings", [])
        if not isinstance(raw, list):
            return []
        findings: list[dict[str, str]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            code = sanitize(str(item.get("code", "GENERAL_REVIEW")), 100).upper()
            findings.append(
                {
                    "code": code,
                    "severity": sanitize(str(item.get("severity", "warning")), 32).casefold(),
                    "summary": sanitize(str(item.get("summary", "Review current Make configuration."))),
                    "recommendation": sanitize(str(item.get("recommendation", "Revalidate against live schema and controlled testing."))),
                }
            )
        return findings

    def _record(self, status: str, findings: list[dict[str, str]], verified: bool) -> dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        seed = json.dumps({"created_at": created_at, "status": status, "findings": findings}, sort_keys=True).encode("utf-8")
        record: dict[str, Any] = {
            "schema_version": 1,
            "id": hashlib.sha256(seed).hexdigest()[:16],
            "created_at": created_at,
            "status": status,
            "kind": "scenario-review",
            "findings": findings,
            "data_policy": "No scenario IDs, names, blueprints, payloads, URLs, credentials, customer data, or free-text verification retained.",
        }
        if verified:
            record["verification"] = "User confirmed a safe resolution; details intentionally not retained."
        return record

    def _append(self, path: Path, record: dict[str, Any]) -> None:
        ensure_private_directory(self.directory)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        try:
            path.chmod(0o600)
        except OSError:
            pass

    def _load_memory(self) -> dict[str, Any]:
        if not self.memory_path.exists():
            return {"schema_version": 1, "themes": {}}
        try:
            value = json.loads(self.memory_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"schema_version": 1, "themes": {}}
        return value if isinstance(value, dict) and isinstance(value.get("themes"), dict) else {"schema_version": 1, "themes": {}}

    def _update_memory(self, findings: list[dict[str, str]], verified: bool) -> None:
        memory = self._load_memory()
        themes: dict[str, Any] = memory["themes"]
        now = datetime.now(timezone.utc).isoformat()
        for finding in findings:
            theme = themes.setdefault(
                finding["code"],
                {
                    "severity": finding["severity"],
                    "summary": finding["summary"],
                    "recommendation": finding["recommendation"],
                    "candidate_count": 0,
                    "verified_count": 0,
                    "last_seen": now,
                },
            )
            theme["candidate_count"] += 1
            if verified:
                theme["verified_count"] += 1
            theme["last_seen"] = now
        write_private_text(self.memory_path, json.dumps(memory, ensure_ascii=False, indent=2) + "\n")

    def _render_personal_skill(self) -> None:
        memory = self._load_memory()
        themes = memory["themes"]
        verified = [(code, value) for code, value in themes.items() if value.get("verified_count", 0)]
        candidate = [(code, value) for code, value in themes.items() if not value.get("verified_count", 0)]
        lines = [
            "# Personal Make Skills Memory",
            "",
            "This is user-local private guidance generated with explicit consent. It is never committed or sent to GitHub.",
            "Read only the verified lessons as advisory context; revalidate all current Make behavior against live MCP/official CLI schema.",
            "",
            "## Verified personal lessons",
            "",
        ]
        if verified:
            for code, item in sorted(verified):
                lines.extend([f"### {code}", "", f"- **Pattern:** {item['summary']}", f"- **Preferred check:** {item['recommendation']}", f"- **Verified observations:** {item['verified_count']}", ""])
        else:
            lines.append("No verified personal lessons yet. Confirm a resolution before treating a pattern as guidance.\n")
        lines.extend(["## Unverified review candidates", "", "These are tracking signals, not instructions. Do not apply them without fresh evidence.", ""])
        if candidate:
            for code, item in sorted(candidate):
                lines.extend([f"- `{code}`: seen {item['candidate_count']} time(s); revalidate before acting."])
        else:
            lines.append("None.")
        write_private_text(self.skill_path, "\n".join(lines).rstrip() + "\n")
