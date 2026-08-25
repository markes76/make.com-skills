from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_upstream_sources.py"
SPEC = importlib.util.spec_from_file_location("check_upstream_sources", SCRIPT)
assert SPEC and SPEC.loader
WATCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WATCH)


def manifest() -> dict:
    return {
        "schema_version": 1,
        "allowed_hosts": {"developers.make.com"},
        "sources": [
            {
                "id": "cli-auth",
                "url": "https://developers.make.com/make-cli/make-cli/authenticate-the-make-cli",
                "kind": "official-cli-guide",
            }
        ],
    }


class UpstreamSourceWatchTests(unittest.TestCase):
    def test_changed_metadata_is_a_review_candidate_and_drops_body_data(self) -> None:
        previous = {
            "schema_version": 1,
            "sources": {
                "cli-auth": {
                    "status": "observed",
                    "status_code": 200,
                    "final_url": "https://developers.make.com/make-cli/make-cli/authenticate-the-make-cli",
                    "etag": "old",
                    "last_modified": "Mon, 01 Jan 2024 00:00:00 GMT",
                    "content_length": "100",
                    "content_type": "text/html",
                }
            },
        }

        def fake_fetch(url: str, allowed_hosts: set, timeout: float) -> dict:
            self.assertEqual(url, "https://developers.make.com/make-cli/make-cli/authenticate-the-make-cli")
            self.assertEqual(allowed_hosts, {"developers.make.com"})
            self.assertGreater(timeout, 0)
            return {
                "status": "observed",
                "status_code": 200,
                "final_url": url,
                "etag": "new",
                "last_modified": "Mon, 01 Jan 2024 00:00:00 GMT",
                "content_length": "100",
                "content_type": "text/html",
                "body": "never-persist-this-article-content",
                "authorization": "never-persist-this-token",
            }

        report, next_state = WATCH.check_sources(manifest(), previous, 1.0, fake_fetch)
        serialized = json.dumps({"report": report, "state": next_state})
        self.assertNotIn("never-persist-this-article-content", serialized)
        self.assertNotIn("never-persist-this-token", serialized)
        self.assertEqual(report["summary"]["candidate_changes"], 1)
        self.assertEqual(report["changes"][0]["classification"], "metadata_changed")
        self.assertEqual(report["changes"][0]["changed_fields"], ["etag"])
        self.assertTrue(report["policy"]["human_review_required"])
        self.assertFalse(report["policy"]["make_operations_performed"])

    def test_write_state_is_explicit_and_does_not_modify_the_manifest(self) -> None:
        source_manifest = ROOT / "sources" / "upstream-manifest.json"
        original_manifest = source_manifest.read_text(encoding="utf-8")
        baseline = {
            "schema_version": 1,
            "manifest_path": "sources/upstream-manifest.json",
            "written_at": "2026-08-25T00:00:00+00:00",
            "policy": {"metadata_only": True, "content_persisted": False},
            "sources": {"cli-auth": {"status": "observed", "status_code": 200}},
        }
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "state.json"
            WATCH.write_json(state_path, baseline)
            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8")), baseline)
        self.assertEqual(source_manifest.read_text(encoding="utf-8"), original_manifest)

    def test_manifest_rejects_non_allowlisted_or_non_https_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "allowed_hosts": ["developers.make.com"],
                        "sources": [{"id": "bad", "url": "http://example.test/", "kind": "test"}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(WATCH.ManifestError):
                WATCH.load_manifest(path)

    def test_manifest_and_reports_reject_or_strip_url_query_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "allowed_hosts": ["developers.make.com"],
                        "sources": [{"id": "bad", "url": "https://developers.make.com/docs?token=secret", "kind": "test"}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(WATCH.ManifestError):
                WATCH.load_manifest(path)
        safe = WATCH.safe_snapshot(
            {"status": "observed", "status_code": 200, "final_url": "https://developers.make.com/docs?token=secret#anchor"}
        )
        self.assertEqual(safe["final_url"], "https://developers.make.com/docs")


if __name__ == "__main__":
    unittest.main()
