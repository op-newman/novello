from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = SKILL_ROOT / "tests" / ".tmp"
LOCKED_TRUTH = "accident_truth"
TOUCH_OBLIGATION = "Lin must touch the old case thread."
TOUCH_EVIDENCE = "Lin touched the old case file."
ENDING_TARGET = "Keep the accident truth locked."
DRAFT_TEXT = (
    "Lin touched the old case file. "
    "The accident truth remained sealed. "
    "Gu chose limited collaboration."
)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class NovelloScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = TMP_ROOT / self._testMethodName
        if self.project.exists():
            shutil.rmtree(self.project)
        self.project.mkdir(parents=True)
        write_json(self.project / "novello.json", {"schema_version": 1, "chapter_digits": 6})

    def tearDown(self) -> None:
        if self.project.exists():
            shutil.rmtree(self.project)

    def run_script(self, name: str, *args: str) -> subprocess.CompletedProcess[str]:
        script = SKILL_ROOT / "scripts" / name
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=SKILL_ROOT,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def seed_card(self) -> None:
        write_json(
            self.project / "cards" / "000001.json",
            {
                "schema_version": 1,
                "chapter_id": 1,
                "title": "Seed",
                "summary": "A long arc is seeded.",
                "events": [
                    {
                        "event_id": "c001_e01",
                        "location": "loc:archive",
                        "participants": ["char:lin"],
                        "text": "Lin saw the old case number.",
                        "evidence": "Lin saw the old case number.",
                    }
                ],
                "entity_changes": [],
                "knowledge_changes": [
                    {
                        "character_id": "char:lin",
                        "fact": "old_case_number_exists",
                        "status": "known",
                        "evidence": "Lin saw the old case number.",
                    }
                ],
                "relationship_changes": [
                    {
                        "pair": ["char:lin", "char:gu"],
                        "from": "distant",
                        "to": "strained_trust",
                        "evidence": "Lin saw the old case number.",
                    }
                ],
                "thread_events": [
                    {
                        "thread_id": "thread:old_case",
                        "action": "seed",
                        "from": "none",
                        "to": "seeded",
                        "priority": "high",
                        "still_locked": [LOCKED_TRUTH],
                        "next_review_chapter": 2,
                        "evidence": "Lin saw the old case number.",
                    }
                ],
                "obligations_in": [],
                "obligations_out": [
                    {
                        "id": "obl:c001_touch_old_case",
                        "text": TOUCH_OBLIGATION,
                        "mode": "resolve_now",
                        "due_chapter": 2,
                    }
                ],
                "locks_asserted": [LOCKED_TRUTH],
            },
        )

    def rebuild_seed(self) -> None:
        self.seed_card()
        rebuild = self.run_script("rebuild_projections.py", "--project-root", str(self.project), "--write")
        self.assertEqual(rebuild.returncode, 0, rebuild.stderr + rebuild.stdout)

    def write_contract(self, **overrides: object) -> None:
        contract = {
            "schema_version": 1,
            "chapter_id": 2,
            "title": "Touch",
            "must_satisfy": [],
            "allowed_thread_moves": [
                {
                    "thread_id": "thread:old_case",
                    "from": "seeded",
                    "allowed_to": ["active"],
                    "forbidden_to": ["truth_revealed"],
                }
            ],
            "relationship_bounds": {
                "char:lin__char:gu": {
                    "current": "strained_trust",
                    "allowed_moves": ["limited_collaboration"],
                    "forbidden_moves": ["formal_love"],
                }
            },
            "knowledge_locks": [LOCKED_TRUTH],
            "required_evidence_in_draft": [],
            "ending_target": ENDING_TARGET,
            "packet_budget_chars": 5000,
        }
        contract.update(overrides)
        write_json(self.project / "contracts" / "000002.json", contract)

    def write_packet(self, **overrides: object) -> None:
        packet = {
            "schema_version": 1,
            "chapter_id": 2,
            "contract_id": "000002",
            "opening_state": "The old case thread remains unresolved.",
            "must_do": [TOUCH_EVIDENCE],
            "must_not_do": [LOCKED_TRUTH],
            "active_entities": ["char:lin", "char:gu"],
            "active_threads": [{"thread_id": "thread:old_case", "state": "seeded"}],
            "relationship_bounds": {"char:lin__char:gu": "limited_collaboration only"},
            "knowledge_limits": {"locked": [LOCKED_TRUTH]},
            "obligations": [
                {"id": "obl:c001_touch_old_case", "text": TOUCH_OBLIGATION, "mode": "resolve_now"}
            ],
            "style_focus": ["restrained"],
            "ending_target": ENDING_TARGET,
            "target_length": "1000 Chinese characters",
        }
        packet.update(overrides)
        write_json(self.project / "packets" / "000002.json", packet)

    def write_draft(self, text: str | None = None) -> None:
        (self.project / "chapters").mkdir(exist_ok=True)
        (self.project / "chapters" / "000002.md").write_text(text or DRAFT_TEXT, encoding="utf-8")

    def write_card(self, **overrides: object) -> None:
        card = {
            "schema_version": 1,
            "chapter_id": 2,
            "title": "Touch",
            "summary": "The old case thread is touched.",
            "events": [],
            "entity_changes": [],
            "knowledge_changes": [],
            "relationship_changes": [
                {
                    "pair": ["char:lin", "char:gu"],
                    "from": "strained_trust",
                    "to": "limited_collaboration",
                    "evidence": "Gu chose limited collaboration.",
                }
            ],
            "thread_events": [
                {
                    "thread_id": "thread:old_case",
                    "action": "touch",
                    "from": "seeded",
                    "to": "active",
                    "still_locked": [LOCKED_TRUTH],
                    "next_review_chapter": 5,
                    "evidence": TOUCH_EVIDENCE,
                }
            ],
            "obligations_in": [{"id": "obl:c001_touch_old_case", "status": "resolved"}],
            "obligations_out": [],
            "locks_asserted": [LOCKED_TRUTH],
        }
        card.update(overrides)
        write_json(self.project / "cards" / "000002.json", card)

    def test_rebuild_and_validate_happy_path(self) -> None:
        self.rebuild_seed()
        self.write_contract(must_satisfy=[TOUCH_OBLIGATION], required_evidence_in_draft=[TOUCH_EVIDENCE])
        self.write_packet(must_do=[TOUCH_OBLIGATION, TOUCH_EVIDENCE])

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")
        self.assertEqual(packet.returncode, 0, packet.stderr + packet.stdout)

        self.write_draft()
        self.write_card()

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")
        self.assertEqual(card.returncode, 0, card.stderr + card.stdout)

        rebuild = self.run_script("rebuild_projections.py", "--project-root", str(self.project), "--write")
        self.assertEqual(rebuild.returncode, 0, rebuild.stderr + rebuild.stdout)

    def test_packet_requires_overdue_thread(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_packet(active_threads=[])

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(packet.returncode, 0)
        self.assertIn("overdue_thread_missing", packet.stdout)

    def test_packet_requires_contract_items(self) -> None:
        self.rebuild_seed()
        self.write_contract(must_satisfy=["Contract-only beat."], ending_target=ENDING_TARGET)
        self.write_packet(must_do=[], ending_target="Different ending.")

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(packet.returncode, 0)
        self.assertIn("contract_must_satisfy_missing", packet.stdout)
        self.assertIn("contract_ending_target_missing", packet.stdout)

    def test_packet_requires_contract_relationship_bounds(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_packet(relationship_bounds={})

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(packet.returncode, 0)
        self.assertIn("contract_relationship_bound_missing", packet.stdout)

    def test_packet_rejects_contradictory_contract(self) -> None:
        self.rebuild_seed()
        self.write_contract(
            allowed_thread_moves=[
                {
                    "thread_id": "thread:old_case",
                    "from": "seeded",
                    "allowed_to": ["active"],
                    "forbidden_to": ["active", "truth_revealed"],
                }
            ],
            relationship_bounds={
                "char:lin__char:gu": {
                    "current": "strained_trust",
                    "allowed_moves": ["limited_collaboration"],
                    "forbidden_moves": ["limited_collaboration"],
                }
            },
        )
        self.write_packet()

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(packet.returncode, 0)
        self.assertIn("contract_thread_move_contradiction", packet.stdout)
        self.assertIn("contract_relationship_bound_contradiction", packet.stdout)

    def test_card_requires_contract_evidence_in_draft(self) -> None:
        self.rebuild_seed()
        self.write_contract(required_evidence_in_draft=["This exact sentence is required."])
        self.write_draft()
        self.write_card()

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("required_evidence_not_in_draft", card.stdout)

    def test_card_rejects_uncontracted_thread_move(self) -> None:
        self.rebuild_seed()
        self.write_contract(allowed_thread_moves=[])
        self.write_draft()
        self.write_card()

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("thread_move_not_in_contract", card.stdout)

    def test_card_rejects_unbounded_relationship_move(self) -> None:
        self.rebuild_seed()
        self.write_contract(relationship_bounds={})
        self.write_draft()
        self.write_card()

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("relationship_change_not_bounded", card.stdout)

    def test_card_requires_evidence_for_projection_changing_event(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card(
            events=[
                {
                    "event_id": "c002_e01",
                    "location": "loc:station",
                    "participants": ["char:lin"],
                    "text": "Lin reached the station.",
                }
            ]
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("event_projection_change_missing_evidence", card.stdout)

    def test_rebuild_rejects_duplicate_and_mismatched_card_source(self) -> None:
        self.seed_card()
        write_json(
            self.project / "cards" / "000002.json",
            {
                "schema_version": 1,
                "chapter_id": 1,
                "title": "Duplicate",
                "summary": "Bad source ordering.",
                "events": [],
                "entity_changes": [],
                "knowledge_changes": [],
                "relationship_changes": [],
                "thread_events": [],
                "obligations_in": [],
                "obligations_out": [],
                "locks_asserted": [],
            },
        )

        rebuild = self.run_script("rebuild_projections.py", "--project-root", str(self.project), "--write")

        self.assertNotEqual(rebuild.returncode, 0)
        self.assertIn("card_filename_chapter_mismatch", rebuild.stdout)
        self.assertIn("duplicate_card_chapter_id", rebuild.stdout)

    def test_rebuild_rejects_card_gaps(self) -> None:
        self.seed_card()
        write_json(
            self.project / "cards" / "000003.json",
            {
                "schema_version": 1,
                "chapter_id": 3,
                "title": "Gap",
                "summary": "Chapter 2 is missing.",
                "events": [],
                "entity_changes": [],
                "knowledge_changes": [],
                "relationship_changes": [],
                "thread_events": [],
                "obligations_in": [],
                "obligations_out": [],
                "locks_asserted": [],
            },
        )

        rebuild = self.run_script("rebuild_projections.py", "--project-root", str(self.project), "--write")

        self.assertNotEqual(rebuild.returncode, 0)
        self.assertIn("card_chapter_gap", rebuild.stdout)

    def test_obligation_resolution_uses_stable_id(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card(obligations_in=[{"id": "obl:c001_touch_old_case", "status": "resolved"}])

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")
        self.assertEqual(card.returncode, 0, card.stderr + card.stdout)

        rebuild = self.run_script("rebuild_projections.py", "--project-root", str(self.project), "--write")
        self.assertEqual(rebuild.returncode, 0, rebuild.stderr + rebuild.stdout)
        obligations = json.loads((self.project / "projections" / "obligations.open.json").read_text(encoding="utf-8"))
        self.assertEqual(obligations, [])

    def test_card_rejects_wrong_obligation_id_resolution(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card(obligations_in=[{"id": "obl:wrong", "status": "resolved"}])

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("resolve_now_obligation_unsettled", card.stdout)

    def test_card_requires_stable_id_for_outgoing_obligations(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card(
            obligations_out=[
                {
                    "text": "Keep the truth locked in chapter 3.",
                    "mode": "avoid_contradiction",
                    "due_chapter": 3,
                }
            ]
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("obligation_id_missing", card.stdout)


if __name__ == "__main__":
    unittest.main()
