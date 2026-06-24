#!/usr/bin/env python3
"""Validate a Novello packet against projections and contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import chapter_digits, force_utf8_stdio, issue, padded, read_json


def contains_text(items: Any, text: str) -> bool:
    return text in json.dumps(items, ensure_ascii=False)


def as_string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def require_fields(obj: Any, fields: list[str], errors: list[dict[str, str]], *, label: str, path: Path) -> None:
    if not isinstance(obj, dict) or not obj:
        return
    for field in fields:
        if field not in obj:
            errors.append(issue(f"{label}_field_missing", f"{label} missing required field: {field}", path=str(path)))


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--chapter-id", type=int, required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root)
    pad = padded(args.chapter_id, chapter_digits(project_root))
    packet_path = project_root / "packets" / f"{pad}.json"
    contract_path = project_root / "contracts" / f"{pad}.json"

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    try:
        packet = read_json(packet_path)
    except FileNotFoundError:
        packet = {}
        errors.append(issue("packet_missing", "Packet file is missing.", path=str(packet_path)))
    try:
        contract = read_json(contract_path)
    except FileNotFoundError:
        contract = {}
        errors.append(issue("contract_missing", "Contract file is missing.", path=str(contract_path)))

    threads = read_json(project_root / "projections" / "threads.current.json", default={})
    obligations = read_json(project_root / "projections" / "obligations.open.json", default=[])

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
        overlap = sorted(as_string_set(bound.get("allowed_moves")) & as_string_set(bound.get("forbidden_moves")))
        if overlap:
            errors.append(
                issue(
                    "contract_relationship_bound_contradiction",
                    f"Relationship bound lists the same move as allowed and forbidden for {key}: {', '.join(overlap)}",
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
        if not isinstance(bound.get("allowed_moves"), list) or not bound["allowed_moves"]:
            errors.append(issue("contract_relationship_bound_missing_allowed_moves", f"Relationship bound missing allowed_moves: {key}"))

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
