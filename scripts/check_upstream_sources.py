#!/usr/bin/env python3
"""Watch a small allowlist of public Make documentation metadata.

This checker is intentionally metadata-only.  It does not read response bodies,
store page content, use authentication, invoke the official Make CLI/MCP, or
perform any Make operation.  A changed HTTP header is a candidate for human
review, not proof that documentation or product behavior changed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "sources" / "upstream-manifest.json"
DEFAULT_STATE = ROOT / "sources" / "upstream-source-state.json"
SCHEMA_VERSION = 1
MAX_HEADER_VALUE_LENGTH = 512
MAX_REDIRECTS = 5
MATERIAL_FIELDS = (
    "status",
    "status_code",
    "final_url",
    "etag",
    "last_modified",
    "content_length",
    "content_type",
)
FALLBACK_TO_GET_STATUS = {403, 405, 501}


class ManifestError(ValueError):
    """The source manifest does not satisfy the strict metadata-only policy."""


class MetadataFetchError(RuntimeError):
    """Fetching metadata could not safely produce an observation."""


class NoRedirect(HTTPRedirectHandler):
    """Return redirects to the caller so each target can be allowlist-checked."""

    def redirect_request(  # type: ignore[override]
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def limit_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    compact = " ".join(str(value).split())
    return compact[:MAX_HEADER_VALUE_LENGTH] if compact else None


def validate_url(url: str, allowed_hosts: Set[str]) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ManifestError("sources must use an absolute HTTPS URL")
    if parsed.username or parsed.password:
        raise ManifestError("source URLs may not contain credentials")
    try:
        port = parsed.port
    except ValueError as error:
        raise ManifestError("source URLs may not contain an invalid port") from error
    if port not in (None, 443):
        raise ManifestError("source URLs may not use a non-default port")
    if parsed.hostname.lower() not in allowed_hosts:
        raise ManifestError("source URL host is not in allowed_hosts")
    if parsed.query or parsed.fragment:
        raise ManifestError("source URLs may not contain query strings or fragments")


def canonical_public_url(value: Optional[str]) -> Optional[str]:
    """Remove query, fragment, and userinfo before a URL can enter a report."""
    if not value:
        return None
    parsed = urlparse(value)
    try:
        port = parsed.port
    except ValueError:
        return None
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or port not in (None, 443):
        return None
    return urlunparse(("https", parsed.hostname.lower(), parsed.path or "/", "", "", ""))


def load_manifest(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestError("could not read a valid JSON manifest") from error

    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ManifestError("manifest schema_version must be 1")
    raw_hosts = payload.get("allowed_hosts")
    raw_sources = payload.get("sources")
    if not isinstance(raw_hosts, list) or not raw_hosts:
        raise ManifestError("manifest requires a non-empty allowed_hosts list")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ManifestError("manifest requires a non-empty sources list")

    allowed_hosts: Set[str] = set()
    for host in raw_hosts:
        if not isinstance(host, str) or not host or "/" in host or ":" in host:
            raise ManifestError("allowed_hosts must contain bare host names")
        allowed_hosts.add(host.lower())

    ids: Set[str] = set()
    sources: List[Dict[str, str]] = []
    for source in raw_sources:
        if not isinstance(source, dict):
            raise ManifestError("each source must be an object")
        source_id = source.get("id")
        url = source.get("url")
        kind = source.get("kind")
        if not all(isinstance(value, str) and value.strip() for value in (source_id, url, kind)):
            raise ManifestError("each source requires non-empty id, url, and kind")
        if source_id in ids:
            raise ManifestError("source IDs must be unique")
        validate_url(url, allowed_hosts)
        ids.add(source_id)
        sources.append({"id": source_id, "url": url, "kind": kind})

    return {"schema_version": SCHEMA_VERSION, "allowed_hosts": allowed_hosts, "sources": sources}


def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "sources": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestError("could not read a valid JSON state file") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ManifestError("state schema_version must be 1")
    if not isinstance(payload.get("sources"), dict):
        raise ManifestError("state requires a sources object")
    return payload


def header_value(headers: Any, name: str) -> Optional[str]:
    try:
        return limit_text(headers.get(name))
    except (AttributeError, TypeError):
        return None


def is_allowed_redirect(url: str, allowed_hosts: Set[str]) -> bool:
    try:
        validate_url(url, allowed_hosts)
        return True
    except ManifestError:
        return False


def open_without_untrusted_redirects(
    url: str,
    method: str,
    allowed_hosts: Set[str],
    timeout: float,
) -> Tuple[Any, str]:
    opener = build_opener(HTTPSHandler(), NoRedirect())
    current_url = url
    headers = {
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.1",
        "User-Agent": "make-com-skills-source-watch/1.0 (+https://github.com/markes76/make.com-skills)",
    }
    if method == "GET":
        # A few servers reject HEAD. Do not read the response body even when
        # this fallback is used; Range makes the request as small as possible.
        headers["Range"] = "bytes=0-0"

    for _ in range(MAX_REDIRECTS + 1):
        request = Request(current_url, headers=headers, method=method)
        try:
            return opener.open(request, timeout=timeout), current_url
        except HTTPError as error:
            if 300 <= error.code < 400:
                location = error.headers.get("Location") if error.headers else None
                error.close()
                if not location:
                    raise MetadataFetchError("redirect_without_location")
                next_url = urljoin(current_url, location)
                if not is_allowed_redirect(next_url, allowed_hosts):
                    raise MetadataFetchError("redirect_outside_allowlist")
                current_url = next_url
                continue
            # HTTP errors are still useful metadata observations. The caller
            # reads only their status and selected headers, then closes them.
            return error, current_url
        except (URLError, OSError) as error:
            raise MetadataFetchError(type(error).__name__.lower()) from error
    raise MetadataFetchError("redirect_limit_exceeded")


def response_snapshot(response: Any, final_url: str, method: str, checked_at: str) -> Dict[str, Any]:
    try:
        status_code = int(response.getcode())
    except (AttributeError, TypeError, ValueError):
        status_code = None
    headers = getattr(response, "headers", None)
    return {
        "status": "observed",
        "checked_at": checked_at,
        "request_method": method,
        "status_code": status_code,
        "final_url": canonical_public_url(final_url),
        "etag": header_value(headers, "ETag"),
        "last_modified": header_value(headers, "Last-Modified"),
        "content_length": header_value(headers, "Content-Length"),
        "content_type": header_value(headers, "Content-Type"),
    }


def fetch_metadata(url: str, allowed_hosts: Set[str], timeout: float) -> Dict[str, Any]:
    """Return selected HTTP metadata without reading a response body."""

    checked_at = utc_now()
    try:
        response, final_url = open_without_untrusted_redirects(url, "HEAD", allowed_hosts, timeout)
        try:
            status_code = int(response.getcode())
            if status_code in FALLBACK_TO_GET_STATUS:
                response.close()
                response, final_url = open_without_untrusted_redirects(url, "GET", allowed_hosts, timeout)
                return response_snapshot(response, final_url, "GET", checked_at)
            return response_snapshot(response, final_url, "HEAD", checked_at)
        finally:
            response.close()
    except MetadataFetchError as error:
        return {
            "status": "unavailable",
            "checked_at": checked_at,
            "error_kind": str(error),
        }


def safe_snapshot(snapshot: Mapping[str, Any]) -> Dict[str, Any]:
    """Drop anything except explicitly approved metadata fields."""

    result: Dict[str, Any] = {}
    for field in MATERIAL_FIELDS:
        value = snapshot.get(field)
        if field in ("status_code",):
            result[field] = value if isinstance(value, int) else None
        elif field == "status":
            result[field] = value if value in {"observed", "unavailable"} else "unavailable"
        elif field == "final_url":
            result[field] = canonical_public_url(value if isinstance(value, str) else None)
        elif value is None or isinstance(value, str):
            result[field] = limit_text(value)
        else:
            result[field] = limit_text(str(value))
    if result["status"] == "unavailable":
        error_kind = snapshot.get("error_kind")
        result["error_kind"] = limit_text(error_kind if isinstance(error_kind, str) else None)
    return result


def changed_fields(before: Mapping[str, Any], after: Mapping[str, Any]) -> List[str]:
    return [field for field in MATERIAL_FIELDS if before.get(field) != after.get(field)]


def classify_change(before: Optional[Mapping[str, Any]], after: Mapping[str, Any]) -> Optional[str]:
    if before is None:
        return "new_source"
    if before.get("status") == "unavailable" and after.get("status") == "observed":
        return "source_recovered"
    if before.get("status") == "observed" and after.get("status") == "unavailable":
        return "source_unavailable"
    if changed_fields(before, after):
        return "metadata_changed"
    return None


Fetcher = Callable[[str, Set[str], float], Dict[str, Any]]


def check_sources(
    manifest: Mapping[str, Any],
    state: Mapping[str, Any],
    timeout: float,
    fetcher: Fetcher = fetch_metadata,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Compare a manifest observation with a state baseline, without writing."""

    previous_sources = state.get("sources", {})
    if not isinstance(previous_sources, dict):
        raise ManifestError("state sources must be an object")

    observations: List[Dict[str, Any]] = []
    changes: List[Dict[str, Any]] = []
    next_sources: Dict[str, Dict[str, Any]] = {}
    for source in manifest["sources"]:
        source_id = source["id"]
        observed = safe_snapshot(fetcher(source["url"], manifest["allowed_hosts"], timeout))
        previous_raw = previous_sources.get(source_id)
        previous = safe_snapshot(previous_raw) if isinstance(previous_raw, dict) else None
        next_sources[source_id] = observed
        observations.append({"id": source_id, "kind": source["kind"], "metadata": observed})
        change_kind = classify_change(previous, observed)
        if change_kind:
            changes.append(
                {
                    "id": source_id,
                    "kind": source["kind"],
                    "classification": change_kind,
                    "changed_fields": changed_fields(previous or {}, observed),
                    "before": previous,
                    "after": observed,
                }
            )

    unavailable = sum(1 for item in observations if item["metadata"]["status"] == "unavailable")
    summary = {
        "checked": len(observations),
        "candidate_changes": len(changes),
        "unavailable": unavailable,
        "unchanged": len(observations) - len(changes),
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "mode": "metadata_only",
        "summary": summary,
        "policy": {
            "response_bodies_read": False,
            "response_bodies_persisted": False,
            "credentials_used": False,
            "make_operations_performed": False,
            "human_review_required": True,
        },
        "changes": changes,
        "observations": observations,
        "limitations": [
            "HTTP metadata can change because of CDN, caching, redirects, or deployment behavior.",
            "A candidate metadata signal is not proof that Make documentation or API behavior changed.",
            "Inspect the official source manually before proposing or accepting guidance changes.",
        ],
    }
    next_state = {
        "schema_version": SCHEMA_VERSION,
        "manifest_path": "sources/upstream-manifest.json",
        "written_at": utc_now(),
        "policy": {
            "metadata_only": True,
            "content_persisted": False,
            "review_required_before_guidance_change": True,
        },
        "sources": next_sources,
    }
    return report, next_state


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as temporary:
        temporary.write(encoded)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check public Make documentation metadata without reading page bodies.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Allowlisted source manifest JSON")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE, help="Committed metadata state JSON")
    parser.add_argument("--report", type=Path, help="Write the JSON report to this file instead of stdout")
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-request timeout in seconds (default: 20)")
    parser.add_argument(
        "--write-state",
        action="store_true",
        help="Explicitly replace the metadata state after this check; no content is scraped or changed.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.timeout <= 0:
        print("ERROR: --timeout must be positive", file=sys.stderr)
        return 1
    try:
        manifest = load_manifest(args.manifest)
        state = load_state(args.state)
        report, next_state = check_sources(manifest, state, args.timeout)
        if args.write_state:
            write_json(args.state, next_state)
            report["state_written"] = str(args.state)
        if args.report:
            write_json(args.report, report)
        else:
            print(json.dumps(report, indent=2, sort_keys=True))
    except (ManifestError, OSError) as error:
        print("ERROR: {0}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
