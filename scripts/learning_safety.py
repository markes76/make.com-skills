"""Strict validation for public, generic Make learning candidates.

Candidates may become a public Git change.  They therefore accept only a
small, generic statement backed by an allowlisted official Make public URL.
They are not an incident-log format and must reject uncertain redaction.
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any
from urllib.parse import urlparse, urlunparse


SCHEMA_VERSION = 2
OFFICIAL_PUBLIC_HOSTS = frozenset({"developers.make.com", "apps.make.com", "help.make.com"})
ALLOWED_KINDS = frozenset({"schema", "runtime", "design", "api", "tooling"})
ALLOWED_ORIGIN = "official_public_documentation"
ALLOWED_REVIEW_STATUS = "pending_maintainer_review"
REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "id",
        "created_at",
        "status",
        "origin",
        "source_url",
        "title",
        "kind",
        "symptom",
        "root_cause",
        "resolution",
        "evidence",
        "expires_after_days",
        "review_status",
    }
)

SECRET = re.compile(r"(?i)\b(?:authorization|api[_ -]?key|token|password|secret)\s*[:=]")
TOKEN_SHAPE = re.compile(r"(?i)\b(?:ghp_[a-z0-9]+|github_pat_[a-z0-9_]+|sk-[a-z0-9_-]+|xox[baprs]-[a-z0-9-]+|AIza[a-z0-9_-]+)\b")
URL = re.compile(r"(?i)https?://")
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d(). -]{6,}\d)(?!\w)")
UUID = re.compile(r"(?i)\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b")
RESOURCE_IDENTIFIER = re.compile(
    r"(?i)\b(?:scenario|team|organization|connection|execution|account|customer|user|contact|record|bundle)[ _-]*(?:id|number)?\s*[:=#]\s*[a-z0-9_-]{3,}\b"
)
REDACTION_MARKER = re.compile(r"\[REDACTED", re.I)


class PublicLearningSafetyError(ValueError):
    """A candidate is not safe to retain or promote as public guidance."""


def canonical_official_source_url(value: str) -> str:
    if not isinstance(value, str):
        raise PublicLearningSafetyError("source_url must be text")
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        raise PublicLearningSafetyError("source_url must be an absolute HTTPS URL")
    if parsed.hostname.lower() not in OFFICIAL_PUBLIC_HOSTS:
        raise PublicLearningSafetyError("source_url must use an allowlisted official Make documentation host")
    try:
        port = parsed.port
    except ValueError as error:
        raise PublicLearningSafetyError("source_url must not contain an invalid port") from error
    if parsed.username or parsed.password or port not in (None, 443):
        raise PublicLearningSafetyError("source_url must not contain credentials or a non-default port")
    if parsed.query or parsed.fragment:
        raise PublicLearningSafetyError("source_url must not contain a query string or fragment")
    return urlunparse(("https", parsed.hostname.lower(), parsed.path or "/", "", "", ""))


def generic_public_text(field: str, value: Any, maximum: int = 800) -> str:
    if not isinstance(value, str):
        raise PublicLearningSafetyError(f"{field} must be text")
    text = " ".join(value.split())
    if not text or len(text) > maximum:
        raise PublicLearningSafetyError(f"{field} must be between 1 and {maximum} characters")
    for pattern, description in (
        (SECRET, "a credential assignment"),
        (TOKEN_SHAPE, "a token-like value"),
        (URL, "a URL; use source_url for the public documentation link"),
        (EMAIL, "an email address"),
        (PHONE, "a phone number"),
        (UUID, "a UUID-like identifier"),
        (RESOURCE_IDENTIFIER, "a resource or customer identifier"),
        (REDACTION_MARKER, "a redaction marker; reject uncertain source material instead"),
    ):
        if pattern.search(text):
            raise PublicLearningSafetyError(f"{field} contains {description}")
    return text


def validate_candidate(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PublicLearningSafetyError("candidate must be an object")
    keys = frozenset(value)
    if keys != REQUIRED_KEYS:
        unexpected = sorted(keys - REQUIRED_KEYS)
        missing = sorted(REQUIRED_KEYS - keys)
        details = []
        if unexpected:
            details.append("unexpected fields: " + ", ".join(unexpected))
        if missing:
            details.append("missing fields: " + ", ".join(missing))
        raise PublicLearningSafetyError("candidate schema mismatch (" + "; ".join(details) + ")")
    if value["schema_version"] != SCHEMA_VERSION or value["status"] != "candidate":
        raise PublicLearningSafetyError("candidate has an unsupported schema version or status")
    if value["origin"] != ALLOWED_ORIGIN or value["review_status"] != ALLOWED_REVIEW_STATUS:
        raise PublicLearningSafetyError("candidate lacks the required public-source review state")
    if not isinstance(value["id"], str) or not re.fullmatch(r"[a-f0-9]{16}", value["id"]):
        raise PublicLearningSafetyError("candidate id is invalid")
    if not isinstance(value["created_at"], str):
        raise PublicLearningSafetyError("candidate created_at is invalid")
    try:
        datetime.fromisoformat(value["created_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise PublicLearningSafetyError("candidate created_at is invalid") from error
    if value["kind"] not in ALLOWED_KINDS:
        raise PublicLearningSafetyError("candidate kind is invalid")
    if value["expires_after_days"] not in {90, 180}:
        raise PublicLearningSafetyError("candidate expiry is invalid")
    return {
        "schema_version": SCHEMA_VERSION,
        "id": value["id"],
        "created_at": value["created_at"],
        "status": "candidate",
        "origin": ALLOWED_ORIGIN,
        "source_url": canonical_official_source_url(value["source_url"]),
        "title": generic_public_text("title", value["title"], 160),
        "kind": value["kind"],
        "symptom": generic_public_text("symptom", value["symptom"]),
        "root_cause": generic_public_text("root_cause", value["root_cause"]),
        "resolution": generic_public_text("resolution", value["resolution"]),
        "evidence": generic_public_text("evidence", value["evidence"]),
        "expires_after_days": value["expires_after_days"],
        "review_status": ALLOWED_REVIEW_STATUS,
    }
