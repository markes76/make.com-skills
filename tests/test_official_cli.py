from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from make_skills.cli import doctor
from make_skills.official_cli import run_json
from make_skills.wizard import write_design_handoff


class OfficialCliBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.binary = self.root / "make-cli"
        self.binary.write_text(
            "#!/bin/sh\n"
            "case \"$1:$2\" in\n"
            "  --version:) echo '1.4.0' ;;\n"
            "  users:me) echo '{\"id\": 7, \"email\": \"private@example.test\"}' ;;\n"
            "  organizations:list) echo '{\"organizations\": [{\"id\": 1, \"name\": \"Example\"}]}' ;;\n"
            "  teams:list) echo '{\"teams\": [{\"id\": 2, \"name\": \"Automation\"}]}' ;;\n"
            "  scenarios:list) echo '{\"scenarios\": []}' ;;\n"
            "  *) echo \"unexpected: $*\" >&2; exit 1 ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        self.binary.chmod(0o755)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_bridge_reads_json_from_the_official_cli(self) -> None:
        result = run_json(["organizations", "list"], str(self.binary))
        self.assertEqual(result["organizations"][0]["id"], 1)

    def test_doctor_does_not_print_user_payload(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(doctor(str(self.binary), as_json=False), 0)
        self.assertIn("Authentication: verified", output.getvalue())
        self.assertNotIn("private@example.test", output.getvalue())

    def test_design_handoff_is_local_and_non_mutating(self) -> None:
        answers = iter(["Route paid orders", "Signed webhook", "CRM upsert and Slack message"])
        messages: list[str] = []
        plan = write_design_handoff(self.root / "plans", lambda _: next(answers), messages.append)
        payload = json.loads(plan.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "design-only")
        self.assertIn("not authorization", payload["safety_note"])
        self.assertNotIn("--api-key", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
