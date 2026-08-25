from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "scripts/record_lesson.py"
PROMOTE = ROOT / "scripts/promote_lesson.py"


def safe_candidate_command(output: Path) -> list[str]:
    return [
        sys.executable,
        str(RECORD),
        "--title", "Authentication check needs a documented zone hostname",
        "--kind", "tooling",
        "--symptom", "The official CLI authentication check is unavailable.",
        "--root-cause", "The selected zone does not match the documented hostname.",
        "--resolution", "Confirm the official zone hostname before retrying the read.",
        "--evidence", "Reproduced with a credential-free local fixture.",
        "--source-url", "https://developers.make.com/make-cli/make-cli/authenticate-the-make-cli",
        "--out", str(output),
    ]


class LearningCandidateTests(unittest.TestCase):
    def test_consent_and_public_safe_source_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidates.jsonl"
            command = safe_candidate_command(output)
            denied = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertNotEqual(denied.returncode, 0)
            created = subprocess.run(command + ["--consent"], capture_output=True, text=True, check=False)
            self.assertEqual(created.returncode, 0, created.stderr)
            record = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(record["schema_version"], 2)
            self.assertEqual(record["origin"], "official_public_documentation")
            self.assertEqual(record["source_url"], "https://developers.make.com/make-cli/make-cli/authenticate-the-make-cli")

    def test_candidate_rejects_personal_or_unknown_source_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidates.jsonl"
            unsafe = safe_candidate_command(output)
            unsafe[unsafe.index("--symptom") + 1] = "Call customer phone +1 555 123 4567 after scenario id: 1905530."
            rejected = subprocess.run(unsafe + ["--consent"], capture_output=True, text=True, check=False)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertFalse(output.exists())
            bad_source = safe_candidate_command(output)
            source_index = bad_source.index("--source-url") + 1
            bad_source[source_index] = "https://example.test/unknown"
            rejected_source = subprocess.run(bad_source + ["--consent"], capture_output=True, text=True, check=False)
            self.assertNotEqual(rejected_source.returncode, 0)

    def test_promotion_requires_a_validated_matching_official_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidates = Path(temporary) / "candidates.jsonl"
            created = subprocess.run(safe_candidate_command(candidates) + ["--consent"], capture_output=True, text=True, check=False)
            self.assertEqual(created.returncode, 0, created.stderr)
            record = json.loads(candidates.read_text(encoding="utf-8"))
            output = Path(temporary) / "approved.md"
            base = [sys.executable, str(PROMOTE), record["id"], "--candidates", str(candidates), "--output", str(output), "--approve"]
            missing_review = subprocess.run(base, capture_output=True, text=True, check=False)
            self.assertNotEqual(missing_review.returncode, 0)
            bad_review = subprocess.run(base + ["--reviewed-source-url", "https://help.make.com/"], capture_output=True, text=True, check=False)
            self.assertNotEqual(bad_review.returncode, 0)
            promoted = subprocess.run(base + ["--reviewed-source-url", record["source_url"]], capture_output=True, text=True, check=False)
            self.assertEqual(promoted.returncode, 0, promoted.stderr)
            self.assertIn(record["source_url"], output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
