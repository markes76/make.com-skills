from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "scripts/record_lesson.py"


class LearningCandidateTests(unittest.TestCase):
    def test_consent_is_required_and_sensitive_strings_are_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidates.jsonl"
            command = [
                sys.executable, str(RECORD), "--title", "403 recovery", "--kind", "runtime",
                "--symptom", "token=top-secret", "--root-cause", "Authorization: Bearer a-real-secret",
                "--resolution", "reconnect", "--evidence", "https://example.test/webhook/very-secret user@example.test",
                "--out", str(output),
            ]
            denied = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertNotEqual(denied.returncode, 0)
            created = subprocess.run(command + ["--consent"], capture_output=True, text=True, check=False)
            self.assertEqual(created.returncode, 0, created.stderr)
            record = json.loads(output.read_text(encoding="utf-8"))
            self.assertNotIn("top-secret", json.dumps(record))
            self.assertNotIn("a-real-secret", json.dumps(record))
            self.assertNotIn("user@example.test", json.dumps(record))
            self.assertEqual(record["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
