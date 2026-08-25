from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from make_skills.cli import doctor, review
from make_skills.official_cli import run_json
from make_skills.personal_learning import PersonalLearningStore
from make_skills.wizard import build_scenario_review, choose, review_scenarios, run_wizard, write_design_handoff, write_scenario_review


class OfficialCliBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.binary = self.root / "make-cli"
        self.binary.write_text(
            "#!/bin/sh\n"
            "if [ -n \"$MAKE_SKILLS_TEST_LOG\" ]; then printf '%s\\n' \"$*\" >> \"$MAKE_SKILLS_TEST_LOG\"; fi\n"
            "case \"$1:$2\" in\n"
            "  --version:) echo '1.4.0' ;;\n"
            "  users:me) echo '{\"id\": 7, \"email\": \"private@example.test\"}' ;;\n"
            "  organizations:list) echo '{\"organizations\": [{\"id\": 1, \"name\": \"Example\"}]}' ;;\n"
            "  teams:list) echo '{\"teams\": [{\"id\": 2, \"name\": \"Automation\"}]}' ;;\n"
            "  scenarios:list) echo '{\"scenarios\": [{\"id\": 99, \"name\": \"Inbound orders\"}]}' ;;\n"
            "  scenarios:get) echo '{\"scenario\": {\"id\": 99, \"name\": \"Inbound orders\", \"active\": false, \"blueprint\": \"{\\\"flow\\\":[{\\\"module\\\":\\\"webhooks-customWebhook\\\"}]}\"}}' ;;\n"
            "  fail:) echo 'token=never-print-this' >&2; exit 9 ;;\n"
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
        self.assertIn("independent community companion", output.getvalue())
        self.assertNotIn("private@example.test", output.getvalue())

    def test_official_cli_failure_does_not_echo_provider_diagnostics(self) -> None:
        with self.assertRaisesRegex(Exception, "exit status 9") as captured:
            run_json(["fail"], str(self.binary))
        self.assertNotIn("never-print-this", str(captured.exception))

    def test_design_handoff_is_local_and_non_mutating(self) -> None:
        answers = iter(["Route paid orders", "Signed webhook", "CRM upsert and Slack message"])
        messages: list[str] = []
        plan = write_design_handoff(self.root / "plans", lambda _: next(answers), messages.append)
        payload = json.loads(plan.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "design-only")
        self.assertIn("not authorization", payload["safety_note"])
        self.assertTrue(any("If MCP cannot perform" in step for step in payload["required_next_steps"]))
        self.assertNotIn("--api-key", json.dumps(payload))

    def test_scenario_review_derives_findings_without_raw_blueprint(self) -> None:
        review = build_scenario_review(
            {
                "scenario": {
                    "id": 99,
                    "name": "Inbound orders",
                    "active": False,
                    "blueprint": json.dumps({"flow": [{"module": "webhooks-customWebhook"}, {"module": "http-makeRequest"}]}),
                }
            }
        )
        self.assertEqual(review["scenario_id"], 99)
        self.assertEqual(review["derived_facts"]["module_count"], 2)
        self.assertNotIn("blueprint", review)
        self.assertNotIn("module_references", review)
        self.assertEqual(review["source"]["official_cli_version"], "not-recorded")
        self.assertEqual(review["input_shape"]["assessment"], "evaluable")
        self.assertTrue(any(item["code"] == "ERROR_HANDLING_NEEDS_VALIDATION" for item in review["findings"]))

    def test_review_filename_cannot_escape_its_private_directory(self) -> None:
        path = write_scenario_review(self.root / "reviews", {"scenario_id": "../../outside", "findings": []}, lambda _: None)
        self.assertEqual(path.parent, self.root / "reviews")
        self.assertTrue(path.name.startswith("scenario-review-outside-"))

    def test_unrecognized_and_malformed_responses_are_not_evaluable(self) -> None:
        malformed = build_scenario_review({"scenario": {"id": 99, "blueprint": "not-json"}})
        unknown = build_scenario_review({"result": "unexpected"})
        self.assertTrue(any(item["code"] == "BLUEPRINT_NOT_EVALUABLE" for item in malformed["findings"]))
        self.assertTrue(any(item["code"] == "RESPONSE_NOT_EVALUABLE" for item in unknown["findings"]))

    def test_module_words_do_not_create_confirmed_heuristic_findings(self) -> None:
        review = build_scenario_review({"scenario": {"id": 99, "blueprint": json.dumps({"flow": [{"module": "webhooks-customWebhook"}]})}})
        self.assertFalse(any("WEBHOOK" in item["code"] for item in review["findings"]))

    def test_scenario_selector_accepts_an_id(self) -> None:
        selected = choose([{"id": 1905530, "name": "Error to email"}], "scenario", lambda _: "1905530", lambda _: None, allow_id=True)
        self.assertEqual(selected["name"], "Error to email")

    def test_scenario_selector_allows_an_id_not_in_the_list(self) -> None:
        selected = choose([{"id": 1905530, "name": "Error to email"}], "scenario", lambda _: "1909999", lambda _: None, allow_id=True)
        self.assertEqual(selected["id"], "1909999")

    def test_scenario_selector_can_force_a_numeric_id(self) -> None:
        selected = choose([{"id": 9, "name": "Ninth"}, {"id": 1, "name": "First"}], "scenario", lambda _: "id:1", lambda _: None, allow_id=True)
        self.assertEqual(selected["name"], "First")

    def test_review_loop_reads_then_writes_only_local_artifacts(self) -> None:
        log = self.root / "commands.log"
        before = os.environ.get("MAKE_SKILLS_TEST_LOG")
        os.environ["MAKE_SKILLS_TEST_LOG"] = str(log)
        try:
            answers = iter(["99", "Add a controlled retry path", "n"])
            messages: list[str] = []
            review_scenarios(
                2,
                str(self.binary),
                self.root / "reviews",
                self.root / "changes",
                None,
                lambda _: next(answers),
                messages.append,
            )
        finally:
            if before is None:
                del os.environ["MAKE_SKILLS_TEST_LOG"]
            else:
                os.environ["MAKE_SKILLS_TEST_LOG"] = before
        reports = list((self.root / "reviews").glob("*.json"))
        changes = list((self.root / "changes").glob("*.json"))
        self.assertEqual(len(reports), 1)
        self.assertEqual(len(changes), 1)
        persisted = reports[0].read_text(encoding="utf-8")
        self.assertNotIn("Inbound orders", persisted)
        self.assertNotIn("webhooks-customWebhook", persisted)
        invoked = log.read_text(encoding="utf-8")
        self.assertIn("scenarios list --team-id 2", invoked)
        self.assertIn("scenarios get 99", invoked)
        self.assertNotIn("scenarios update", invoked)
        self.assertNotIn("scenarios run", invoked)

    def test_noninteractive_review_is_read_only_unless_save_is_requested(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(review(str(self.binary), "99", self.root / "reports", as_json=True, save=False), 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["source"]["official_cli_version"], "1.4.0")
        self.assertFalse((self.root / "reports").exists())

    def test_wizard_returns_to_menu_after_one_selected_scenario_review(self) -> None:
        answers = iter(["1", "1", "n", "1", "99", "", "n", "4"])
        messages: list[str] = []
        run_wizard(
            str(self.binary),
            self.root / "plans",
            self.root / "reviews",
            self.root / "changes",
            ask=lambda _: next(answers),
            say=messages.append,
        )
        rendered = "\n".join(messages)
        self.assertEqual(rendered.count("1 scenario(s) returned for team 2."), 1)
        self.assertIn("Review: 99 (Inbound orders)", rendered)
        self.assertIn("independent community companion", rendered)
        self.assertIn("No Make changes were made.", rendered)

    def test_private_learning_omits_scenario_identity_and_redacts(self) -> None:
        store = PersonalLearningStore(self.root / "private")
        review = {
            "scenario_id": 99,
            "scenario_name": "Customer email flow",
            "findings": [
                {
                    "code": "ERROR_HANDLING_NEEDS_VALIDATION",
                    "severity": "warning",
                    "summary": "token=secret-value for user@example.test",
                    "recommendation": "Inspect the failure route.",
                }
            ],
        }
        store.record_review(review)
        candidate = store.candidates_path.read_text(encoding="utf-8")
        self.assertNotIn("Customer email flow", candidate)
        self.assertNotIn('"scenario_id"', candidate)
        self.assertNotIn("secret-value", candidate)
        store.record_verified_resolution(review, "Controlled test passed with token=private")
        verified = store.verified_path.read_text(encoding="utf-8")
        self.assertNotIn("Controlled test passed", verified)
        self.assertNotIn("private", verified)
        self.assertIn("ERROR_HANDLING_NEEDS_VALIDATION", store.skill_path.read_text(encoding="utf-8"))
        if os.name != "nt":
            self.assertEqual(store.directory.stat().st_mode & 0o777, 0o700)
            self.assertEqual(store.skill_path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
