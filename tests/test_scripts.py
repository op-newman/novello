from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
import uuid
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
        self.project = TMP_ROOT / f"{self._testMethodName}_{uuid.uuid4().hex}"
        self.project.mkdir(parents=True)
        write_json(self.project / "novello.json", {"schema_version": 1, "language": "zh-CN", "chapter_digits": 6})

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
                "evidence": [
                    {"id": "ev_seed", "quote": "Lin saw the old case number."},
                ],
                "events": [
                    {
                        "event_id": "c001_e01",
                        "location": "loc:archive",
                        "participants": ["char:lin"],
                        "text": "Lin saw the old case number.",
                        "evidence_ref": "ev_seed",
                    }
                ],
                "entity_changes": [],
                "knowledge_changes": [
                    {
                        "character_id": "char:lin",
                        "fact": "old_case_number_exists",
                        "status": "known",
                        "evidence_ref": "ev_seed",
                    }
                ],
                "relationship_changes": [
                    {
                        "pair": ["char:lin", "char:gu"],
                        "from": "distant",
                        "to": "strained_trust",
                        "evidence_ref": "ev_seed",
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
                        "evidence_ref": "ev_seed",
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
            "target_language": "zh-CN",
            "target_length": "1000 characters",
        }
        packet.update(overrides)
        write_json(self.project / "packets" / "000002.json", packet)

    def write_draft(self, text: str | None = None) -> None:
        (self.project / "chapters").mkdir(exist_ok=True)
        (self.project / "chapters" / "000002.md").write_text(text or DRAFT_TEXT, encoding="utf-8")

    def write_review(self, text: str | None = None) -> None:
        review = text or """# Chapter 2 Review

## Verdict
pass

## Issues
- none

## Contract Experience
- Contract-only beat: satisfied

## Notes
No new canon.

## RetconScan
- durable_new_fact: none - no durable fact outside the contract.
- knowledge_leak: none - no locked fact leaks.
- relationship_jump: none - relationship stays bounded.
- obligation_change: none - no obligation is changed.
- new_reader_promise: none - no new reader promise.

retcon_verdict: pass
"""
        (self.project / "reviews").mkdir(exist_ok=True)
        (self.project / "reviews" / "000002.md").write_text(review, encoding="utf-8")

    def write_card(self, **overrides: object) -> None:
        card = {
            "schema_version": 1,
            "chapter_id": 2,
            "title": "Touch",
            "summary": "The old case thread is touched.",
            "evidence": [
                {"id": "ev_touch", "quote": TOUCH_EVIDENCE},
                {"id": "ev_rel", "quote": "Gu chose limited collaboration."},
            ],
            "events": [],
            "entity_changes": [],
            "knowledge_changes": [],
            "relationship_changes": [
                {
                    "pair": ["char:lin", "char:gu"],
                    "from": "strained_trust",
                    "to": "limited_collaboration",
                    "evidence_ref": "ev_rel",
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
                    "evidence_ref": "ev_touch",
                }
            ],
            "obligations_in": [
                {
                    "id": "obl:c001_touch_old_case",
                    "status": "resolved",
                    "evidence_ref": "ev_touch",
                }
            ],
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

    def test_packet_accepts_beat_only_relationship_bound(self) -> None:
        self.rebuild_seed()
        self.write_contract(
            relationship_bounds={
                "char:lin__char:gu": {
                    "current": "strained_trust",
                    "allowed_moves": [],
                    "allowed_relationship_beats": ["toward_limited_collaboration"],
                    "forbidden_moves": ["formal_love"],
                    "forbid_phase_transition": True,
                }
            }
        )
        self.write_packet()

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertEqual(packet.returncode, 0, packet.stderr + packet.stdout)

    def test_packet_rejects_empty_relationship_bound_without_beats_or_transition_ban(self) -> None:
        self.rebuild_seed()
        self.write_contract(
            relationship_bounds={
                "char:lin__char:gu": {
                    "current": "strained_trust",
                    "allowed_moves": [],
                    "forbidden_moves": ["formal_love"],
                }
            }
        )
        self.write_packet()

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(packet.returncode, 0)
        self.assertIn("contract_relationship_bound_missing_allowed_moves", packet.stdout)

    def test_packet_rejects_project_language_mismatch(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_packet(target_language="en-US")

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(packet.returncode, 0)
        self.assertIn("packet_target_language_mismatch", packet.stdout)

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

    def test_card_accepts_evidence_refs(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card()

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")
        data = json.loads(card.stdout)

        self.assertEqual(card.returncode, 0, card.stderr + card.stdout)
        self.assertEqual(data["warnings"], [])
        self.assertEqual(data["stats"]["evidence_count"], 2)

    def test_card_rejects_missing_evidence_ref(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card(
            thread_events=[
                {
                    "thread_id": "thread:old_case",
                    "action": "touch",
                    "from": "seeded",
                    "to": "active",
                    "still_locked": [LOCKED_TRUTH],
                    "next_review_chapter": 5,
                    "evidence_ref": "ev_missing",
                }
            ]
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("evidence_ref_missing", card.stdout)

    def test_card_requires_valid_evidence_pool(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card(evidence=None)

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("evidence_pool_invalid", card.stdout)

    def test_card_rejects_duplicate_evidence_ids(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card(
            evidence=[
                {"id": "ev_touch", "quote": TOUCH_EVIDENCE},
                {"id": "ev_touch", "quote": "Gu chose limited collaboration."},
            ]
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("evidence_id_duplicate", card.stdout)

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
        self.assertFalse((self.project / "projections" / "entities.current.json").exists())

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
        self.assertFalse((self.project / "projections" / "entities.current.json").exists())

    def test_obligation_resolution_uses_stable_id(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card(
            obligations_in=[
                {
                    "id": "obl:c001_touch_old_case",
                    "status": "resolved",
                    "evidence_ref": "ev_touch",
                }
            ]
        )

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
        self.write_card(obligations_in=[{"id": "obl:wrong", "status": "resolved", "evidence_ref": "ev_touch"}])

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("resolve_now_obligation_unsettled", card.stdout)

    def test_card_requires_evidence_for_obligation_resolution(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card(obligations_in=[{"id": "obl:c001_touch_old_case", "status": "resolved"}])

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("obligation_resolution_missing_evidence", card.stdout)

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

    def seed_card_with_due_obligation(self) -> None:
        """Seed chapter 1 with a non-resolve_now obligation due at chapter 2."""
        write_json(
            self.project / "cards" / "000001.json",
            {
                "schema_version": 1,
                "chapter_id": 1,
                "title": "Seed",
                "summary": "A long-range promise is planted.",
                "evidence": [
                    {"id": "ev_promise", "quote": "Lin promised to return the key."},
                ],
                "events": [],
                "entity_changes": [],
                "knowledge_changes": [],
                "relationship_changes": [],
                "thread_events": [],
                "obligations_in": [],
                "obligations_out": [
                    {
                        "id": "obl:c001_archive_key_return",
                        "type": "reader_promise",
                        "text": "Lin must return or explain the archive key.",
                        "mode": "maintain_pressure",
                        "due_chapter": 2,
                        "planted_evidence_ref": "ev_promise",
                        "fulfillment_conditions": ["Lin returns the key", "OR Lin explains why she cannot"],
                    }
                ],
                "locks_asserted": [],
            },
        )
        rebuild = self.run_script("rebuild_projections.py", "--project-root", str(self.project), "--write")
        self.assertEqual(rebuild.returncode, 0, rebuild.stderr + rebuild.stdout)

    def test_card_rejects_unsettled_due_obligation(self) -> None:
        self.seed_card_with_due_obligation()
        self.write_contract(allowed_thread_moves=[], relationship_bounds={})
        self.write_draft()
        self.write_card(relationship_changes=[], thread_events=[], obligations_in=[])

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("due_obligation_unsettled", card.stdout)

    def test_rebuild_expands_reader_promise_planted_evidence_ref(self) -> None:
        self.seed_card_with_due_obligation()

        obligations = json.loads((self.project / "projections" / "obligations.open.json").read_text(encoding="utf-8"))

        self.assertEqual(obligations[0]["planted_evidence"], "Lin promised to return the key.")
        self.assertNotIn("planted_evidence_ref", obligations[0])

    def test_card_accepts_settled_due_obligation(self) -> None:
        self.seed_card_with_due_obligation()
        self.write_contract(allowed_thread_moves=[], relationship_bounds={})
        self.write_draft()
        self.write_card(
            relationship_changes=[],
            thread_events=[],
            obligations_in=[
                {
                    "id": "obl:c001_archive_key_return",
                    "status": "resolved",
                    "evidence_ref": "ev_touch",
                }
            ],
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertEqual(card.returncode, 0, card.stderr + card.stdout)

    def test_card_rejects_reader_promise_without_planted_evidence(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card(
            obligations_out=[
                {
                    "id": "obl:c002_future_promise",
                    "type": "reader_promise",
                    "text": "Resolve the future promise.",
                    "mode": "maintain_pressure",
                    "source_chapter": 2,
                    "due_chapter": 4,
                    "fulfillment_conditions": ["The promise is kept."],
                }
            ]
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("reader_promise_missing_planted_evidence", card.stdout)

    def test_card_rejects_reader_promise_planted_evidence_absent_from_draft(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card(
            obligations_out=[
                {
                    "id": "obl:c002_future_promise",
                    "type": "reader_promise",
                    "text": "Resolve the future promise.",
                    "mode": "maintain_pressure",
                    "source_chapter": 2,
                    "due_chapter": 4,
                    "planted_evidence_ref": "ev_bad",
                    "fulfillment_conditions": ["The promise is kept."],
                }
            ],
            evidence=[
                {"id": "ev_touch", "quote": TOUCH_EVIDENCE},
                {"id": "ev_rel", "quote": "Gu chose limited collaboration."},
                {"id": "ev_bad", "quote": "This promise is not in the draft."},
            ],
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("reader_promise_planted_evidence_not_in_draft", card.stdout)

    def test_card_accepts_reader_promise_planted_evidence_ref(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_draft()
        self.write_card(
            obligations_out=[
                {
                    "id": "obl:c002_promise",
                    "type": "reader_promise",
                    "text": "Lin must keep the promise.",
                    "mode": "resolve_now",
                    "source_chapter": 2,
                    "due_chapter": 4,
                    "planted_evidence_ref": "ev_touch",
                    "fulfillment_conditions": ["The promise is kept."],
                }
            ]
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertEqual(card.returncode, 0, card.stderr + card.stdout)

    def test_card_accepts_relationship_beat(self) -> None:
        self.rebuild_seed()
        self.write_contract(allowed_thread_moves=[])
        self.write_draft()
        self.write_card(
            thread_events=[],
            relationship_changes=[
                {
                    "type": "relationship_beat",
                    "pair": ["char:lin", "char:gu"],
                    "current_phase": "strained_trust",
                    "direction": "toward_limited_collaboration",
                    "intensity": "small",
                    "evidence_ref": "ev_rel",
                }
            ],
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertEqual(card.returncode, 0, card.stderr + card.stdout)

    def test_card_accepts_explicitly_allowed_relationship_beat(self) -> None:
        self.rebuild_seed()
        self.write_contract(
            allowed_thread_moves=[],
            relationship_bounds={
                "char:lin__char:gu": {
                    "current": "strained_trust",
                    "allowed_moves": [],
                    "allowed_relationship_beats": ["toward_limited_collaboration"],
                    "forbidden_moves": ["formal_love"],
                    "forbid_phase_transition": True,
                }
            },
        )
        self.write_draft()
        self.write_card(
            thread_events=[],
            relationship_changes=[
                {
                    "type": "relationship_beat",
                    "pair": ["char:lin", "char:gu"],
                    "current_phase": "strained_trust",
                    "direction": "toward_limited_collaboration",
                    "intensity": "small",
                    "evidence_ref": "ev_rel",
                }
            ],
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertEqual(card.returncode, 0, card.stderr + card.stdout)

    def test_card_rejects_unlisted_relationship_beat_when_contract_whitelists_beats(self) -> None:
        self.rebuild_seed()
        self.write_contract(
            allowed_thread_moves=[],
            relationship_bounds={
                "char:lin__char:gu": {
                    "current": "strained_trust",
                    "allowed_moves": [],
                    "allowed_relationship_beats": ["toward_limited_collaboration"],
                    "forbidden_moves": ["formal_love"],
                    "forbid_phase_transition": True,
                }
            },
        )
        self.write_draft()
        self.write_card(
            thread_events=[],
            relationship_changes=[
                {
                    "type": "relationship_beat",
                    "pair": ["char:lin", "char:gu"],
                    "current_phase": "strained_trust",
                    "direction": "toward_private_rescue",
                    "intensity": "small",
                    "evidence_ref": "ev_rel",
                }
            ],
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("relationship_beat_not_allowed", card.stdout)

    def test_card_rejects_phase_transition_when_contract_only_allows_relationship_beat(self) -> None:
        self.rebuild_seed()
        self.write_contract(
            relationship_bounds={
                "char:lin__char:gu": {
                    "current": "strained_trust",
                    "allowed_moves": [],
                    "allowed_relationship_beats": ["toward_limited_collaboration"],
                    "forbidden_moves": ["formal_love"],
                    "forbid_phase_transition": True,
                }
            }
        )
        self.write_draft()
        self.write_card()

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("relationship_move_not_allowed", card.stdout)

    def test_card_rejects_relationship_beat_with_transition(self) -> None:
        self.rebuild_seed()
        self.write_contract(allowed_thread_moves=[])
        self.write_draft()
        self.write_card(
            thread_events=[],
            relationship_changes=[
                {
                    "type": "relationship_beat",
                    "pair": ["char:lin", "char:gu"],
                    "current_phase": "strained_trust",
                    "to": "limited_collaboration",
                    "direction": "toward_limited_collaboration",
                    "intensity": "small",
                    "evidence_ref": "ev_rel",
                }
            ],
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("relationship_beat_has_transition", card.stdout)

    def test_card_rejects_relationship_beat_phase_mismatch(self) -> None:
        self.rebuild_seed()
        self.write_contract(allowed_thread_moves=[])
        self.write_draft()
        self.write_card(
            thread_events=[],
            relationship_changes=[
                {
                    "type": "relationship_beat",
                    "pair": ["char:lin", "char:gu"],
                    "current_phase": "limited_collaboration",
                    "direction": "toward_mutual_trust",
                    "intensity": "small",
                    "evidence_ref": "ev_rel",
                }
            ],
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("relationship_beat_phase_mismatch", card.stdout)

    def test_rebuild_accumulates_relationship_beats(self) -> None:
        self.rebuild_seed()
        self.write_contract(allowed_thread_moves=[])
        self.write_draft()
        self.write_card(
            thread_events=[],
            relationship_changes=[
                {
                    "type": "relationship_beat",
                    "pair": ["char:lin", "char:gu"],
                    "current_phase": "strained_trust",
                    "direction": "toward_limited_collaboration",
                    "intensity": "small",
                    "evidence_ref": "ev_rel",
                }
            ],
        )

        rebuild = self.run_script("rebuild_projections.py", "--project-root", str(self.project), "--write")
        self.assertEqual(rebuild.returncode, 0, rebuild.stderr + rebuild.stdout)

        relationships = json.loads(
            (self.project / "projections" / "relationships.current.json").read_text(encoding="utf-8")
        )
        pair = relationships["char:lin__char:gu"]
        self.assertEqual(pair["phase"], "strained_trust")
        self.assertEqual(len(pair["recent_beats"]), 1)
        self.assertEqual(pair["recent_beats"][0]["chapter_id"], 2)
        self.assertEqual(pair["recent_beats"][0]["evidence"], "Gu chose limited collaboration.")

    def test_packet_rejects_too_many_style_anchors(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_packet(
            style_anchors=[
                {"chapter_id": 1, "excerpt": "a", "reason": "x"},
                {"chapter_id": 1, "excerpt": "b", "reason": "x"},
                {"chapter_id": 1, "excerpt": "c", "reason": "x"},
                {"chapter_id": 1, "excerpt": "d", "reason": "x"},
            ]
        )

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(packet.returncode, 0)
        self.assertIn("style_anchors_too_many", packet.stdout)

    def test_packet_accepts_valid_style_anchors(self) -> None:
        self.rebuild_seed()
        self.write_contract(must_satisfy=[TOUCH_OBLIGATION], required_evidence_in_draft=[TOUCH_EVIDENCE])
        self.write_packet(
            must_do=[TOUCH_OBLIGATION, TOUCH_EVIDENCE],
            style_anchors=[
                {"chapter_id": 1, "excerpt": "A short representative excerpt.", "reason": "restrained POV"}
            ],
        )

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertEqual(packet.returncode, 0, packet.stderr + packet.stdout)

    def test_packet_rejects_invalid_dramatic_guidance(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_packet(non_canon_dramatic_guidance="make it tense")

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(packet.returncode, 0)
        self.assertIn("dramatic_guidance_invalid", packet.stdout)

    def test_packet_accepts_valid_dramatic_guidance(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_packet(
            non_canon_dramatic_guidance={
                "chapter_function": "pressure the old case without opening the locked truth",
                "primary_tension_to_dramatize": "Lin needs Gu's help but cannot explain why",
                "subtext_to_suggest_not_confirm": ["trust is tested through restraint"],
                "reader_experience_goal": "quiet pressure",
                "ending_effect_goal": "the sealed truth feels closer but still withheld",
            }
        )

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertEqual(packet.returncode, 0, packet.stderr + packet.stdout)

    def test_packet_warns_when_dramatic_guidance_may_state_fact(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_packet(
            non_canon_dramatic_guidance={
                "subtext_to_suggest_not_confirm": ["Lin already knows the truth but hides it"]
            }
        )

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertEqual(packet.returncode, 0, packet.stderr + packet.stdout)
        self.assertIn("dramatic_guidance_may_state_fact", packet.stdout)

    def test_packet_rejects_invalid_risk_level(self) -> None:
        self.rebuild_seed()
        self.write_contract(risk_level="catastrophic")
        self.write_packet()

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(packet.returncode, 0)
        self.assertIn("contract_risk_level_invalid", packet.stdout)

    def test_card_rejects_known_locked_fact(self) -> None:
        self.rebuild_seed()
        self.write_contract(allowed_thread_moves=[], relationship_bounds={})
        self.write_draft()
        self.write_card(
            relationship_changes=[],
            thread_events=[],
            obligations_in=[],
            knowledge_changes=[
                {
                    "character_id": "char:lin",
                    "fact": LOCKED_TRUTH,
                    "status": "known",
                    "evidence": "Lin touched the old case file.",
                }
            ],
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("knowledge_lock_violated", card.stdout)

    def test_card_accepts_suspected_locked_fact(self) -> None:
        self.rebuild_seed()
        self.write_contract(allowed_thread_moves=[], relationship_bounds={})
        self.write_draft()
        self.write_card(
            relationship_changes=[],
            thread_events=[],
            obligations_in=[
                {"id": "obl:c001_touch_old_case", "status": "resolved", "evidence_ref": "ev_touch"}
            ],
            knowledge_changes=[
                {
                    "character_id": "char:lin",
                    "fact": LOCKED_TRUTH,
                    "status": "suspected",
                    "evidence_ref": "ev_touch",
                }
            ],
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertEqual(card.returncode, 0, card.stderr + card.stdout)

    def test_card_accepts_known_locked_fact_when_revealed(self) -> None:
        self.rebuild_seed()
        self.write_contract(
            allowed_thread_moves=[],
            relationship_bounds={},
            allowed_reveals=[LOCKED_TRUTH],
            knowledge_locks=[],
        )
        self.write_draft()
        self.write_card(
            relationship_changes=[],
            thread_events=[],
            obligations_in=[
                {"id": "obl:c001_touch_old_case", "status": "resolved", "evidence_ref": "ev_touch"}
            ],
            knowledge_changes=[
                {
                    "character_id": "char:lin",
                    "fact": LOCKED_TRUTH,
                    "status": "known",
                    "evidence_ref": "ev_touch",
                }
            ],
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertEqual(card.returncode, 0, card.stderr + card.stdout)

    def test_card_rejects_beat_toward_forbidden_move(self) -> None:
        self.rebuild_seed()
        self.write_contract(allowed_thread_moves=[])
        self.write_draft()
        self.write_card(
            thread_events=[],
            relationship_changes=[
                {
                    "type": "relationship_beat",
                    "pair": ["char:lin", "char:gu"],
                    "current_phase": "strained_trust",
                    "direction": "toward_formal_love",
                    "intensity": "small",
                    "evidence_ref": "ev_rel",
                }
            ],
        )

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("relationship_beat_direction_forbidden", card.stdout)

    def test_validate_packet_rebuild_as_of_ignores_target_chapter_obligations(self) -> None:
        self.rebuild_seed()
        self.write_contract(must_satisfy=[TOUCH_OBLIGATION], required_evidence_in_draft=[TOUCH_EVIDENCE])
        self.write_packet(must_do=[TOUCH_OBLIGATION, TOUCH_EVIDENCE])
        self.write_draft()
        self.write_card(
            obligations_out=[
                {
                    "id": "obl:c002_future",
                    "text": "Future obligation created by chapter 2.",
                    "mode": "resolve_now",
                    "source_chapter": 2,
                    "due_chapter": 3,
                    "evidence": TOUCH_EVIDENCE,
                }
            ]
        )
        rebuild = self.run_script("rebuild_projections.py", "--project-root", str(self.project), "--write")
        self.assertEqual(rebuild.returncode, 0, rebuild.stderr + rebuild.stdout)

        ordinary = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")
        as_of = self.run_script(
            "validate_packet.py",
            "--project-root",
            str(self.project),
            "--chapter-id",
            "2",
            "--rebuild-as-of",
        )

        self.assertNotEqual(ordinary.returncode, 0)
        self.assertIn("obl:c002_future", ordinary.stdout)
        self.assertEqual(as_of.returncode, 0, as_of.stderr + as_of.stdout)

    def test_validate_card_rejects_duplicate_contract_key(self) -> None:
        self.rebuild_seed()
        contract_path = self.project / "contracts" / "000002.json"
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_path.write_text(
            '{"schema_version":1,"chapter_id":2,"title":"x","must_satisfy":[],"must_satisfy":[]}',
            encoding="utf-8",
        )
        self.write_draft()
        self.write_card()

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(card.returncode, 0)
        self.assertIn("contract_json_duplicate_key", card.stdout)

    def test_validate_packet_rejects_duplicate_packet_key(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        packet_path = self.project / "packets" / "000002.json"
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_path.write_text('{"schema_version":1,"chapter_id":2,"chapter_id":2}', encoding="utf-8")

        packet = self.run_script("validate_packet.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(packet.returncode, 0)
        self.assertIn("packet_json_duplicate_key", packet.stdout)

    def test_card_must_satisfy_trace_is_stat_not_warning(self) -> None:
        self.rebuild_seed()
        self.write_contract(must_satisfy=["Semantic beat only."])
        self.write_draft()
        self.write_card()

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")
        data = json.loads(card.stdout)

        self.assertEqual(card.returncode, 0, card.stderr + card.stdout)
        self.assertNotIn("semantic_must_satisfy_review_items", {item["code"] for item in data["warnings"]})
        self.assertEqual(data["stats"]["semantic_must_satisfy_review_items"], 1)

    def test_card_reports_compactness_stats_and_soft_budget_warnings(self) -> None:
        self.rebuild_seed()
        write_json(
            self.project / "novello.json",
            {
                "schema_version": 1,
                "language": "zh-CN",
                "chapter_digits": 6,
                "card_soft_budget_chars": 200,
                "card_soft_projection_items": 1,
                "card_soft_evidence_items": 1,
            },
        )
        self.write_contract()
        self.write_draft()
        self.write_card()

        card = self.run_script("validate_card.py", "--project-root", str(self.project), "--chapter-id", "2")
        data = json.loads(card.stdout)
        warning_codes = {item["code"] for item in data["warnings"]}

        self.assertEqual(card.returncode, 0, card.stderr + card.stdout)
        self.assertIn("card_chars", data["stats"])
        self.assertIn("projection_items", data["stats"])
        self.assertIn("card_over_soft_budget", warning_codes)
        self.assertIn("card_many_projection_items", warning_codes)
        self.assertIn("card_many_evidence_items", warning_codes)

    def test_suggest_evidence_returns_exact_chinese_sentence_from_draft(self) -> None:
        self.write_draft("青禾把米倒进罐里。\n\n这口饭先稳住。阿稷低头看着碗。")

        result = self.run_script(
            "suggest_evidence.py",
            "--project-root",
            str(self.project),
            "--chapter-id",
            "2",
            "--query",
            "稳住",
        )
        data = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(data["results"][0]["evidence"], "这口饭先稳住。")
        self.assertIn(data["results"][0]["evidence"], (self.project / "chapters" / "000002.md").read_text(encoding="utf-8"))

    def test_suggest_evidence_splits_chinese_semicolon(self) -> None:
        self.write_draft("青禾看了水口；阿稷记住泥草。明日再请里正。")

        result = self.run_script(
            "suggest_evidence.py",
            "--project-root",
            str(self.project),
            "--chapter-id",
            "2",
            "--query",
            "泥草",
        )
        data = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(data["results"][0]["evidence"], "阿稷记住泥草。")

    def test_suggest_evidence_reports_missing_draft(self) -> None:
        result = self.run_script(
            "suggest_evidence.py",
            "--project-root",
            str(self.project),
            "--chapter-id",
            "2",
            "--query",
            "稳住",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("draft_missing", result.stdout)

    def test_validate_review_accepts_valid_retcon_scan(self) -> None:
        self.write_review()

        result = self.run_script("validate_review.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_validate_review_rejects_missing_retcon_field(self) -> None:
        self.write_review(
            """# Chapter 2 Review

## Verdict
pass

## Issues
- none

## Contract Experience
- Contract-only beat: satisfied

## Notes
No new canon.

## RetconScan
- durable_new_fact: none - no durable fact outside the contract.
- knowledge_leak: none - no locked fact leaks.
- relationship_jump: none - relationship stays bounded.
- obligation_change: none - no obligation is changed.

retcon_verdict: pass
"""
        )

        result = self.run_script("validate_review.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("retcon_field_missing", result.stdout)

    def test_validate_review_rejects_invalid_retcon_value(self) -> None:
        self.write_review(
            """# Chapter 2 Review

## Verdict
pass

## Issues
- none

## Contract Experience
- Contract-only beat: satisfied

## Notes
No new canon.

## RetconScan
- durable_new_fact: maybe - no durable fact outside the contract.
- knowledge_leak: none - no locked fact leaks.
- relationship_jump: none - relationship stays bounded.
- obligation_change: none - no obligation is changed.
- new_reader_promise: none - no new reader promise.

retcon_verdict: pass
"""
        )

        result = self.run_script("validate_review.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("retcon_field_invalid", result.stdout)

    def test_validate_review_rejects_pass_with_found_retcon_issue(self) -> None:
        self.write_review(
            """# Chapter 2 Review

## Verdict
pass

## Issues
- none

## Contract Experience
- Contract-only beat: satisfied

## Notes
No new canon.

## RetconScan
- durable_new_fact: found - draft created a durable fact outside contract.
- knowledge_leak: none - no locked fact leaks.
- relationship_jump: none - relationship stays bounded.
- obligation_change: none - no obligation is changed.
- new_reader_promise: none - no new reader promise.

retcon_verdict: pass
"""
        )

        result = self.run_script("validate_review.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("retcon_pass_with_found_issue", result.stdout)

    def test_validate_review_accepts_pass_with_suspected_retcon_warning(self) -> None:
        self.write_review(
            """# Chapter 2 Review

## Verdict
pass

## Issues
- none

## Contract Experience
- Contract-only beat: satisfied

## Notes
No new canon.

## RetconScan
- durable_new_fact: suspected - wording may imply a durable fact but remains ambiguous.
- knowledge_leak: none - no locked fact leaks.
- relationship_jump: none - relationship stays bounded.
- obligation_change: none - no obligation is changed.
- new_reader_promise: none - no new reader promise.

retcon_verdict: pass
"""
        )

        result = self.run_script("validate_review.py", "--project-root", str(self.project), "--chapter-id", "2")
        data = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("retcon_pass_with_suspected_issue", {item["code"] for item in data["warnings"]})

    def test_validate_review_rejects_pass_with_high_issue(self) -> None:
        self.write_review(
            """# Chapter 2 Review

## Verdict
pass

## Issues
- severity: high
  type: ending
  evidence: "bad ending"
  note: "ending missed"
  revision_instruction: "revise ending"

## Contract Experience
- Contract-only beat: missing

## Notes
No new canon.

## RetconScan
- durable_new_fact: none - no durable fact outside the contract.
- knowledge_leak: none - no locked fact leaks.
- relationship_jump: none - relationship stays bounded.
- obligation_change: none - no obligation is changed.
- new_reader_promise: none - no new reader promise.

retcon_verdict: pass
"""
        )

        result = self.run_script("validate_review.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review_pass_with_high_issue", result.stdout)

    def test_validate_review_rejects_pass_with_retcon_revise(self) -> None:
        self.write_review(
            """# Chapter 2 Review

## Verdict
pass

## Issues
- none

## Contract Experience
- Contract-only beat: satisfied

## Notes
No new canon.

## RetconScan
- durable_new_fact: suspected - wording should be clarified.
- knowledge_leak: none - no locked fact leaks.
- relationship_jump: none - relationship stays bounded.
- obligation_change: none - no obligation is changed.
- new_reader_promise: none - no new reader promise.

retcon_verdict: revise
"""
        )

        result = self.run_script("validate_review.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review_pass_with_failed_retcon", result.stdout)

    def test_append_run_log_requires_passed_reports(self) -> None:
        self.rebuild_seed()
        self.write_contract()
        self.write_packet()
        self.write_draft()
        self.write_review()
        self.write_card()
        write_json(self.project / "reports" / "packet.json", {"passed": True, "errors": [], "warnings": [], "stats": {}})
        write_json(self.project / "reports" / "card.json", {"passed": True, "errors": [], "warnings": [], "stats": {}})
        write_json(self.project / "reports" / "projection.json", {"passed": True, "errors": [], "stats": {}})

        result = self.run_script(
            "append_run_log.py",
            "--project-root",
            str(self.project),
            "--chapter-id",
            "2",
            "--run-id",
            "test_ch2",
            "--packet-report",
            str(self.project / "reports" / "packet.json"),
            "--card-report",
            str(self.project / "reports" / "card.json"),
            "--projection-report",
            str(self.project / "reports" / "projection.json"),
        )
        line = (self.project / "logs" / "runs.jsonl").read_text(encoding="utf-8").strip()
        record = json.loads(line)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["run_id"], "test_ch2")

    def test_append_run_log_rejects_missing_reports(self) -> None:
        self.write_contract()
        self.write_packet()
        self.write_draft()
        self.write_review()
        self.write_card()

        result = self.run_script("append_run_log.py", "--project-root", str(self.project), "--chapter-id", "2")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("packet_report_missing", result.stdout)
        self.assertFalse((self.project / "logs" / "runs.jsonl").exists())

    def test_append_run_log_rejects_failed_report(self) -> None:
        self.write_contract()
        self.write_packet()
        self.write_draft()
        self.write_review()
        self.write_card()
        write_json(self.project / "reports" / "packet.json", {"passed": True, "errors": [], "warnings": [], "stats": {}})
        write_json(self.project / "reports" / "card.json", {"passed": False, "errors": [{"code": "bad"}], "warnings": [], "stats": {}})
        write_json(self.project / "reports" / "projection.json", {"passed": True, "errors": [], "stats": {}})

        result = self.run_script(
            "append_run_log.py",
            "--project-root",
            str(self.project),
            "--chapter-id",
            "2",
            "--packet-report",
            str(self.project / "reports" / "packet.json"),
            "--card-report",
            str(self.project / "reports" / "card.json"),
            "--projection-report",
            str(self.project / "reports" / "projection.json"),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("card_report_not_passed", result.stdout)
        self.assertFalse((self.project / "logs" / "runs.jsonl").exists())

    def test_append_run_log_rejects_missing_report_path(self) -> None:
        self.write_contract()
        self.write_packet()
        self.write_draft()
        self.write_review()
        self.write_card()
        write_json(self.project / "reports" / "packet.json", {"passed": True, "errors": [], "warnings": [], "stats": {}})
        write_json(self.project / "reports" / "card.json", {"passed": True, "errors": [], "warnings": [], "stats": {}})

        result = self.run_script(
            "append_run_log.py",
            "--project-root",
            str(self.project),
            "--chapter-id",
            "2",
            "--packet-report",
            str(self.project / "reports" / "packet.json"),
            "--card-report",
            str(self.project / "reports" / "card.json"),
            "--projection-report",
            str(self.project / "reports" / "missing.json"),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("report_missing", result.stdout)
        self.assertFalse((self.project / "logs" / "runs.jsonl").exists())

    def test_append_run_log_rejects_non_pass_review(self) -> None:
        self.write_contract()
        self.write_packet()
        self.write_draft()
        self.write_review(
            """# Chapter 2 Review

## Verdict
revise

## Issues
- severity: high
  type: ending
  evidence: "bad ending"
  note: "ending missed"
  revision_instruction: "revise ending"

## Contract Experience
- Contract-only beat: missing

## Notes
No new canon.

## RetconScan
- durable_new_fact: none - no durable fact outside the contract.
- knowledge_leak: none - no locked fact leaks.
- relationship_jump: none - relationship stays bounded.
- obligation_change: none - no obligation is changed.
- new_reader_promise: none - no new reader promise.

retcon_verdict: pass
"""
        )
        self.write_card()
        write_json(self.project / "reports" / "packet.json", {"passed": True, "errors": [], "warnings": [], "stats": {}})
        write_json(self.project / "reports" / "card.json", {"passed": True, "errors": [], "warnings": [], "stats": {}})
        write_json(self.project / "reports" / "projection.json", {"passed": True, "errors": [], "stats": {}})

        result = self.run_script(
            "append_run_log.py",
            "--project-root",
            str(self.project),
            "--chapter-id",
            "2",
            "--packet-report",
            str(self.project / "reports" / "packet.json"),
            "--card-report",
            str(self.project / "reports" / "card.json"),
            "--projection-report",
            str(self.project / "reports" / "projection.json"),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review_verdict_not_passed", result.stdout)
        self.assertFalse((self.project / "logs" / "runs.jsonl").exists())

    def test_append_run_log_accepts_utf16_reports_from_powershell_redirection(self) -> None:
        self.write_contract()
        self.write_packet()
        self.write_draft()
        self.write_review()
        self.write_card()
        packet_report = json.dumps({"passed": True, "errors": [], "warnings": [], "stats": {}}, ensure_ascii=False)
        card_report = json.dumps({"passed": True, "errors": [], "warnings": [], "stats": {}}, ensure_ascii=False)
        projection_report = json.dumps({"passed": True, "errors": [], "stats": {}}, ensure_ascii=False)
        (self.project / "reports").mkdir(exist_ok=True)
        (self.project / "reports" / "packet.json").write_text(packet_report, encoding="utf-16")
        (self.project / "reports" / "card.json").write_text(card_report, encoding="utf-16")
        (self.project / "reports" / "projection.json").write_text(projection_report, encoding="utf-16")

        result = self.run_script(
            "append_run_log.py",
            "--project-root",
            str(self.project),
            "--chapter-id",
            "2",
            "--packet-report",
            str(self.project / "reports" / "packet.json"),
            "--card-report",
            str(self.project / "reports" / "card.json"),
            "--projection-report",
            str(self.project / "reports" / "projection.json"),
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue((self.project / "logs" / "runs.jsonl").exists())

    def test_generate_chapter_plan_uses_due_obligations_and_threads(self) -> None:
        self.rebuild_seed()
        write_json(
            self.project / "plans" / "global_plan.json",
            {
                "schema_version": 1,
                "major_arcs": [
                    {"id": "arc:test", "chapters": "1-5", "promise": "Resolve the test arc slowly."}
                ],
            },
        )

        result = self.run_script(
            "generate_chapter_plan.py",
            "--project-root",
            str(self.project),
            "--chapter-id",
            "2",
            "--write",
        )
        data = json.loads(result.stdout)
        plan = json.loads((self.project / "plans" / "chapters" / "000002.json").read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(data["wrote_plan"])
        self.assertIn("obl:c001_touch_old_case", data["plan"]["generator_notes"]["due_obligation_ids"])
        self.assertIn("thread:old_case", data["plan"]["generator_notes"]["due_thread_ids"])
        self.assertIn("thread:old_case", plan["plot_threads_advanced"])
        self.assertIn(LOCKED_TRUTH, plan["forbidden_reveals"])

    def test_generate_chapter_plan_does_not_overwrite_existing_plan_by_default(self) -> None:
        write_json(self.project / "plans" / "chapters" / "000002.json", {"schema_version": 1, "chapter_id": 2})

        result = self.run_script(
            "generate_chapter_plan.py",
            "--project-root",
            str(self.project),
            "--chapter-id",
            "2",
            "--write",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("plan_already_exists", result.stdout)


if __name__ == "__main__":
    unittest.main()
