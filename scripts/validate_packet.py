#!/usr/bin/env python3
"""Validate a Novello packet against projections and contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import DuplicateKeyError, chapter_digits, force_utf8_stdio, issue, load_cards, padded, read_json


def contains_text(items: Any, text: str) -> bool:
    return text in json.dumps(items, ensure_ascii=False)


def as_string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def validate_short_string(
    value: Any,
    *,
    field: str,
    errors: list[dict[str, str]],
    max_len: int = 300,
    required: bool = False,
) -> None:
    if value is None:
        if required:
            errors.append(issue("dramatic_guidance_field_missing", f"non_canon_dramatic_guidance missing field: {field}"))
        return
    if not isinstance(value, str):
        errors.append(issue("dramatic_guidance_field_invalid", f"non_canon_dramatic_guidance.{field} must be a string."))
    elif len(value) > max_len:
        errors.append(issue("dramatic_guidance_field_too_long", f"non_canon_dramatic_guidance.{field} exceeds {max_len} characters."))


def require_fields(obj: Any, fields: list[str], errors: list[dict[str, str]], *, label: str, path: Path) -> None:
    if not isinstance(obj, dict) or not obj:
        return
    for field in fields:
        if field not in obj:
            errors.append(issue(f"{label}_field_missing", f"{label} missing required field: {field}", path=str(path)))


def replay_projection_until(project_root: Path, max_chapter_exclusive: int) -> tuple[dict[str, Any], list[dict[str, str]]]:
    # Keep this intentionally narrow: validate_packet only needs threads and
    # obligations. Full projection rebuild remains owned by rebuild_projections.py.
    cards, errors = load_cards(project_root)
    threads: dict[str, Any] = {}
    obligations: list[dict[str, Any]] = []

    def ensure_thread(thread_id: str) -> dict[str, Any]:
        return threads.setdefault(
            thread_id,
            {
                "thread_id": thread_id,
                "status": "active",
                "priority": "medium",
                "current_state": "",
                "last_touched_chapter": None,
                "next_review_chapter": None,
                "locked_until_reveal": [],
                "open_questions": [],
            },
        )

    for card in cards:
        chapter_id = card.get("chapter_id")
        if not isinstance(chapter_id, int) or chapter_id >= max_chapter_exclusive:
            continue
        for event in card.get("thread_events", []) or []:
            if not isinstance(event, dict):
                continue
            thread_id = event.get("thread_id")
            if not isinstance(thread_id, str):
                continue
            thread = ensure_thread(thread_id)
            thread["last_touched_chapter"] = chapter_id
            for field in ("status", "priority"):
                if isinstance(event.get(field), str):
                    thread[field] = event[field]
            if isinstance(event.get("to"), str):
                thread["state"] = event["to"]
                thread["current_state"] = event.get("summary") or event["to"]
            if isinstance(event.get("next_review_chapter"), int):
                thread["next_review_chapter"] = event["next_review_chapter"]
            if isinstance(event.get("still_locked"), list):
                thread["locked_until_reveal"] = [x for x in event["still_locked"] if isinstance(x, str)]
            if isinstance(event.get("open_questions"), list):
                thread["open_questions"] = [x for x in event["open_questions"] if isinstance(x, str)]

        for obligation in card.get("obligations_in", []) or []:
            if isinstance(obligation, dict) and obligation.get("status") in {"resolved", "superseded"}:
                target_id = obligation.get("id")
                target_text = obligation.get("text")
                if isinstance(target_id, str) and target_id.strip():
                    obligations = [item for item in obligations if item.get("id") != target_id]
                elif isinstance(target_text, str) and target_text.strip():
                    obligations = [item for item in obligations if item.get("text") != target_text]

        for obligation in card.get("obligations_out", []) or []:
            if isinstance(obligation, dict):
                item = dict(obligation)
                item.setdefault("source_chapter", chapter_id)
                item.setdefault("status", "open")
                obligations.append(item)

    return {"threads": threads, "obligations": obligations}, errors


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--chapter-id", type=int, required=True)
    parser.add_argument(
        "--rebuild-as-of",
        action="store_true",
        help="Rebuild packet validation memory from cards before the target chapter, avoiding completed-target self-obligations.",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root)
    pad = padded(args.chapter_id, chapter_digits(project_root))
    packet_path = project_root / "packets" / f"{pad}.json"
    contract_path = project_root / "contracts" / f"{pad}.json"

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    try:
        packet = read_json(packet_path)
    except DuplicateKeyError as exc:
        packet = {}
        errors.append(issue("packet_json_duplicate_key", f"Packet JSON has duplicate key: {exc.key}", path=str(packet_path)))
    except FileNotFoundError:
        packet = {}
        errors.append(issue("packet_missing", "Packet file is missing.", path=str(packet_path)))
    try:
        contract = read_json(contract_path)
    except DuplicateKeyError as exc:
        contract = {}
        errors.append(issue("contract_json_duplicate_key", f"Contract JSON has duplicate key: {exc.key}", path=str(contract_path)))
    except FileNotFoundError:
        contract = {}
        errors.append(issue("contract_missing", "Contract file is missing.", path=str(contract_path)))

    if args.rebuild_as_of:
        projection, projection_errors = replay_projection_until(project_root, args.chapter_id)
        errors.extend(projection_errors)
        threads = projection["threads"]
        obligations = projection["obligations"]
    else:
        threads = read_json(project_root / "projections" / "threads.current.json", default={})
        obligations = read_json(project_root / "projections" / "obligations.open.json", default=[])
    config = read_json(project_root / "novello.json", default={})
    project_language = config.get("language") if isinstance(config, dict) else None

    if packet.get("chapter_id") != args.chapter_id:
        errors.append(issue("packet_chapter_mismatch", "Packet chapter_id does not match target.", path=str(packet_path)))
    if contract.get("chapter_id") != args.chapter_id:
        errors.append(issue("contract_chapter_mismatch", "Contract chapter_id does not match target.", path=str(contract_path)))
    require_fields(
        packet,
        [
            "schema_version",
            "chapter_id",
            "contract_id",
            "opening_state",
            "must_do",
            "must_not_do",
            "active_entities",
            "active_threads",
            "relationship_bounds",
            "knowledge_limits",
            "obligations",
            "style_focus",
            "ending_target",
            "target_language",
            "target_length",
        ],
        errors,
        label="packet",
        path=packet_path,
    )
    require_fields(
        contract,
        [
            "schema_version",
            "chapter_id",
            "title",
            "must_satisfy",
            "allowed_thread_moves",
            "relationship_bounds",
            "knowledge_locks",
            "required_evidence_in_draft",
            "ending_target",
            "packet_budget_chars",
        ],
        errors,
        label="contract",
        path=contract_path,
    )
    if packet and packet.get("schema_version") != 1:
        errors.append(issue("packet_schema_version_invalid", "Packet schema_version must be 1.", path=str(packet_path)))
    if contract and contract.get("schema_version") != 1:
        errors.append(issue("contract_schema_version_invalid", "Contract schema_version must be 1.", path=str(contract_path)))
    if packet and packet.get("contract_id") not in {pad, str(args.chapter_id)}:
        warnings.append(issue("packet_contract_id_unusual", "Packet contract_id does not match padded or raw chapter id."))
    target_language = packet.get("target_language") if isinstance(packet, dict) else None
    if packet and not (isinstance(target_language, str) and target_language.strip()):
        errors.append(issue("packet_target_language_invalid", "Packet target_language must be a non-empty string.", path=str(packet_path)))
    if isinstance(project_language, str) and project_language.strip() and isinstance(target_language, str):
        if target_language.strip() != project_language.strip():
            errors.append(
                issue(
                    "packet_target_language_mismatch",
                    f"Packet target_language {target_language!r} does not match novello.json language {project_language!r}.",
                    path=str(packet_path),
                )
            )

    reveal_lock_overlap = sorted(as_string_set(contract.get("allowed_reveals")) & as_string_set(contract.get("knowledge_locks")))
    if reveal_lock_overlap:
        errors.append(
            issue(
                "contract_lock_reveal_contradiction",
                "Contract lists the same item as allowed reveal and knowledge lock: " + ", ".join(reveal_lock_overlap),
            )
        )

    for move in contract.get("allowed_thread_moves", []) if isinstance(contract, dict) else []:
        if not isinstance(move, dict):
            continue
        thread_id = move.get("thread_id", "<unknown>")
        if not isinstance(move.get("thread_id"), str) or not move["thread_id"].strip():
            errors.append(issue("contract_thread_move_missing_thread_id", "Allowed thread move lacks thread_id."))
        if not isinstance(move.get("allowed_to"), list) or not move["allowed_to"]:
            errors.append(issue("contract_thread_move_missing_allowed_to", f"Allowed thread move lacks allowed_to for {thread_id}."))
        overlap = sorted(as_string_set(move.get("allowed_to")) & as_string_set(move.get("forbidden_to")))
        if overlap:
            errors.append(
                issue(
                    "contract_thread_move_contradiction",
                    f"Thread move lists the same state as allowed and forbidden for {thread_id}: {', '.join(overlap)}",
                )
            )

    bounds = contract.get("relationship_bounds", {}) if isinstance(contract.get("relationship_bounds"), dict) else {}
    for key, bound in bounds.items():
        if not isinstance(bound, dict):
            continue
        allowed_moves = bound.get("allowed_moves")
        forbidden_moves = bound.get("forbidden_moves")
        allowed_beats = bound.get("allowed_relationship_beats")
        forbid_phase_transition = bound.get("forbid_phase_transition")
        overlap = sorted(as_string_set(allowed_moves) & as_string_set(forbidden_moves))
        if overlap:
            errors.append(
                issue(
                    "contract_relationship_bound_contradiction",
                    f"Relationship bound lists the same move as allowed and forbidden for {key}: {', '.join(overlap)}",
                )
            )
        if allowed_beats is not None and not isinstance(allowed_beats, list):
            errors.append(issue("contract_relationship_bound_invalid_allowed_beats", f"allowed_relationship_beats must be a list for {key}"))
        if forbid_phase_transition is not None and not isinstance(forbid_phase_transition, bool):
            errors.append(issue("contract_relationship_bound_invalid_forbid_phase_transition", f"forbid_phase_transition must be a boolean for {key}"))
        if forbid_phase_transition is True and isinstance(allowed_moves, list) and allowed_moves:
            errors.append(issue("contract_relationship_bound_transition_contradiction", f"{key} forbids phase transition but still lists allowed_moves."))
        if isinstance(allowed_beats, list):
            for beat in allowed_beats:
                if not isinstance(beat, str):
                    errors.append(issue("contract_relationship_bound_invalid_allowed_beat", f"allowed_relationship_beats entries must be strings for {key}"))
                    continue
                for forbidden in as_string_set(forbidden_moves):
                    if forbidden and forbidden in beat:
                        errors.append(
                            issue(
                                "contract_relationship_beat_contradiction",
                                f"Relationship beat {beat!r} pushes toward forbidden move {forbidden!r} for {key}.",
                            )
                        )

    budget = contract.get("packet_budget_chars", 5000)
    packet_chars = len(json.dumps(packet, ensure_ascii=False))
    if isinstance(budget, int) and packet_chars > budget:
        errors.append(issue("packet_over_budget", f"Packet has {packet_chars} chars, over budget {budget}."))

    for item in contract.get("must_satisfy", []) if isinstance(contract, dict) else []:
        if isinstance(item, str) and item.strip() and not contains_text(packet.get("must_do", []), item) and not contains_text(packet, item):
            errors.append(issue("contract_must_satisfy_missing", f"Contract must_satisfy item missing from packet: {item}"))

    ending_target = contract.get("ending_target") if isinstance(contract, dict) else None
    packet_ending = packet.get("ending_target") if isinstance(packet, dict) else None
    if isinstance(ending_target, str) and ending_target.strip():
        if not isinstance(packet_ending, str) or ending_target not in packet_ending:
            errors.append(issue("contract_ending_target_missing", f"Contract ending_target missing from packet: {ending_target}"))

    packet_bounds = packet.get("relationship_bounds", {}) if isinstance(packet.get("relationship_bounds"), dict) else {}
    for key in bounds:
        if key not in packet_bounds and not contains_text(packet_bounds, key):
            errors.append(issue("contract_relationship_bound_missing", f"Contract relationship bound missing from packet: {key}"))

    for key, bound in bounds.items():
        if not isinstance(bound, dict):
            errors.append(issue("contract_relationship_bound_invalid", f"Relationship bound must be an object: {key}"))
            continue
        if not isinstance(bound.get("current"), str) or not bound["current"].strip():
            errors.append(issue("contract_relationship_bound_missing_current", f"Relationship bound missing current state: {key}"))
        allowed_moves = bound.get("allowed_moves")
        allowed_beats = bound.get("allowed_relationship_beats")
        beat_only = isinstance(allowed_beats, list) and any(isinstance(item, str) and item.strip() for item in allowed_beats)
        no_transition = bound.get("forbid_phase_transition") is True
        if not isinstance(allowed_moves, list):
            errors.append(issue("contract_relationship_bound_missing_allowed_moves", f"Relationship bound missing allowed_moves: {key}"))
        elif not allowed_moves and not beat_only and not no_transition:
            errors.append(
                issue(
                    "contract_relationship_bound_missing_allowed_moves",
                    f"Relationship bound needs allowed_moves, allowed_relationship_beats, or forbid_phase_transition: {key}",
                )
            )

    packet_obligations = packet.get("obligations", []) if isinstance(packet, dict) else []
    for obligation in obligations if isinstance(obligations, list) else []:
        if not isinstance(obligation, dict):
            continue
        mode = obligation.get("mode")
        obligation_id = obligation.get("id")
        text = obligation.get("text")
        due = obligation.get("due_chapter")
        required = mode in {"resolve_now", "avoid_contradiction"} or (isinstance(due, int) and due <= args.chapter_id)
        if required and isinstance(obligation_id, str) and obligation_id.strip():
            if not contains_text(packet_obligations, obligation_id):
                errors.append(issue("missing_required_obligation", f"Packet omits required obligation id: {obligation_id}"))
        elif required and isinstance(text, str) and text.strip() and not contains_text(packet_obligations, text):
            errors.append(issue("missing_required_obligation", f"Packet omits required obligation: {text}"))

    active_threads = packet.get("active_threads", []) if isinstance(packet, dict) else []
    must_not_do = packet.get("must_not_do", []) if isinstance(packet, dict) else []
    knowledge_limits = packet.get("knowledge_limits", {}) if isinstance(packet, dict) else {}
    for thread_id, thread in threads.items() if isinstance(threads, dict) else []:
        if not isinstance(thread, dict):
            continue
        priority = thread.get("priority")
        next_review = thread.get("next_review_chapter")
        if priority == "high" and isinstance(next_review, int) and next_review <= args.chapter_id:
            if not contains_text(active_threads, thread_id):
                errors.append(issue("overdue_thread_missing", f"High-priority overdue thread missing from packet: {thread_id}"))
        for lock in thread.get("locked_until_reveal", []) or []:
            if isinstance(lock, str) and not contains_text(must_not_do, lock) and not contains_text(knowledge_limits, lock):
                warnings.append(issue("thread_lock_not_explicit", f"Thread lock not explicit in packet: {lock}"))

    for lock in contract.get("knowledge_locks", []) if isinstance(contract, dict) else []:
        if isinstance(lock, str) and not contains_text(must_not_do, lock) and not contains_text(knowledge_limits, lock):
            errors.append(issue("contract_lock_missing", f"Contract knowledge lock missing from packet: {lock}"))

    excerpts = packet.get("old_prose_excerpts", []) if isinstance(packet, dict) else []
    if excerpts:
        if not isinstance(excerpts, list):
            errors.append(issue("old_prose_excerpts_invalid", "old_prose_excerpts must be a list."))
        elif len(excerpts) > 3:
            errors.append(issue("old_prose_excerpts_too_many", "Packet includes more than 3 old prose excerpts."))
        else:
            for index, excerpt in enumerate(excerpts):
                if len(json.dumps(excerpt, ensure_ascii=False)) > 900:
                    errors.append(issue("old_prose_excerpt_too_long", "Old prose excerpt exceeds 900 serialized chars.", path=f"old_prose_excerpts[{index}]"))

    anchors = packet.get("style_anchors", []) if isinstance(packet, dict) else []
    if anchors:
        if not isinstance(anchors, list):
            errors.append(issue("style_anchors_invalid", "style_anchors must be a list."))
        elif len(anchors) > 3:
            errors.append(issue("style_anchors_too_many", "Packet includes more than 3 style anchors."))
        else:
            for index, anchor in enumerate(anchors):
                if not isinstance(anchor, dict):
                    errors.append(issue("style_anchor_invalid", "Each style anchor must be an object.", path=f"style_anchors[{index}]"))
                    continue
                excerpt = anchor.get("excerpt")
                if not (isinstance(excerpt, str) and excerpt.strip()):
                    errors.append(issue("style_anchor_missing_excerpt", "Style anchor needs a non-empty excerpt.", path=f"style_anchors[{index}]"))
                elif len(excerpt) > 400:
                    errors.append(issue("style_anchor_excerpt_too_long", "Style anchor excerpt exceeds 400 chars; keep it to a short representative sample.", path=f"style_anchors[{index}]"))

    guidance = packet.get("non_canon_dramatic_guidance") if isinstance(packet, dict) else None
    if guidance is not None:
        if not isinstance(guidance, dict):
            errors.append(issue("dramatic_guidance_invalid", "non_canon_dramatic_guidance must be an object."))
        else:
            allowed_guidance_fields = {
                "chapter_function",
                "primary_tension_to_dramatize",
                "subtext_to_suggest_not_confirm",
                "reader_experience_goal",
                "ending_effect_goal",
            }
            for field in guidance:
                if field not in allowed_guidance_fields:
                    warnings.append(issue("dramatic_guidance_unknown_field", f"Unknown non_canon_dramatic_guidance field: {field}"))
            validate_short_string(guidance.get("chapter_function"), field="chapter_function", errors=errors)
            validate_short_string(guidance.get("primary_tension_to_dramatize"), field="primary_tension_to_dramatize", errors=errors)
            validate_short_string(guidance.get("reader_experience_goal"), field="reader_experience_goal", errors=errors)
            validate_short_string(guidance.get("ending_effect_goal"), field="ending_effect_goal", errors=errors)

            subtext = guidance.get("subtext_to_suggest_not_confirm", [])
            if subtext is None:
                subtext = []
            if not isinstance(subtext, list):
                errors.append(issue("dramatic_guidance_subtext_invalid", "non_canon_dramatic_guidance.subtext_to_suggest_not_confirm must be a list."))
            elif len(subtext) > 5:
                errors.append(issue("dramatic_guidance_subtext_too_many", "non_canon_dramatic_guidance includes more than 5 subtext items."))
            else:
                fact_like_terms = ("已", "已经", "知道", "确认", "真相", "身份", "becomes", "knows", "confirmed", "already")
                for index, item in enumerate(subtext):
                    if not isinstance(item, str):
                        errors.append(issue("dramatic_guidance_subtext_item_invalid", "Each subtext_to_suggest_not_confirm item must be a string.", path=f"subtext_to_suggest_not_confirm[{index}]"))
                        continue
                    if len(item) > 180:
                        errors.append(issue("dramatic_guidance_subtext_item_too_long", "Subtext guidance item exceeds 180 characters.", path=f"subtext_to_suggest_not_confirm[{index}]"))
                    if any(term in item for term in fact_like_terms):
                        warnings.append(
                            issue(
                                "dramatic_guidance_may_state_fact",
                                "Subtext guidance may be stating a durable fact; phrase it as something to suggest, test, pressure, or withhold.",
                                path=f"subtext_to_suggest_not_confirm[{index}]",
                            )
                        )

    risk_level = contract.get("risk_level") if isinstance(contract, dict) else None
    if risk_level is not None and risk_level not in {"low", "medium", "high"}:
        errors.append(issue("contract_risk_level_invalid", "Contract risk_level, when present, must be one of: low, medium, high.", path=str(contract_path)))
    requires_review = contract.get("requires_adversarial_review") if isinstance(contract, dict) else None
    if requires_review is not None and not isinstance(requires_review, bool):
        errors.append(issue("contract_requires_adversarial_review_invalid", "Contract requires_adversarial_review, when present, must be a boolean.", path=str(contract_path)))

    result = {
        "schema_version": 1,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {"packet_chars": packet_chars},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
