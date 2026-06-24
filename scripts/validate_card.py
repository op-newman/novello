#!/usr/bin/env python3
"""Validate a Novello chapter card against contract, projection, and draft."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import chapter_digits, force_utf8_stdio, issue, padded, read_json


def evidence_values(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        evidence = value.get("evidence")
        if isinstance(evidence, str) and evidence.strip():
            found.append(evidence.strip())
        for child in value.values():
            found.extend(evidence_values(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(evidence_values(child))
    return found


def pair_key(pair: Any) -> str | None:
    if isinstance(pair, list) and len(pair) == 2 and all(isinstance(item, str) for item in pair):
        return "__".join(pair)
    return None


def contains_text(items: Any, text: str) -> bool:
    return text in json.dumps(items, ensure_ascii=False)


def require_fields(obj: Any, fields: list[str], errors: list[dict[str, str]], *, label: str, path: Path) -> None:
    if not isinstance(obj, dict) or not obj:
        return
    for field in fields:
        if field not in obj:
            errors.append(issue(f"{label}_field_missing", f"{label} missing required field: {field}", path=str(path)))


def item_has_evidence(item: Any) -> bool:
    return isinstance(item, dict) and isinstance(item.get("evidence"), str) and bool(item["evidence"].strip())


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--chapter-id", type=int, required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root)
    pad = padded(args.chapter_id, chapter_digits(project_root))
    card_path = project_root / "cards" / f"{pad}.json"
    draft_path = project_root / "chapters" / f"{pad}.md"
    contract_path = project_root / "contracts" / f"{pad}.json"

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    try:
        card = read_json(card_path)
    except FileNotFoundError:
        card = {}
        errors.append(issue("card_missing", "Card file is missing.", path=str(card_path)))
    try:
        contract = read_json(contract_path)
    except FileNotFoundError:
        contract = {}
        errors.append(issue("contract_missing", "Contract file is missing.", path=str(contract_path)))
    try:
        draft = draft_path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        draft = ""
        errors.append(issue("draft_missing", "Draft/chapter file is missing.", path=str(draft_path)))

    threads = read_json(project_root / "projections" / "threads.current.json", default={})
    obligations = read_json(project_root / "projections" / "obligations.open.json", default=[])

    if card.get("chapter_id") != args.chapter_id:
        errors.append(issue("card_chapter_mismatch", "Card chapter_id does not match target.", path=str(card_path)))
    require_fields(
        card,
        [
            "schema_version",
            "chapter_id",
            "title",
            "summary",
            "events",
            "entity_changes",
            "knowledge_changes",
            "relationship_changes",
            "thread_events",
            "obligations_in",
            "obligations_out",
            "locks_asserted",
        ],
        errors,
        label="card",
        path=card_path,
    )
    if card and card.get("schema_version") != 1:
        errors.append(issue("card_schema_version_invalid", "Card schema_version must be 1.", path=str(card_path)))

    for evidence in evidence_values(card):
        if evidence not in draft:
            errors.append(issue("evidence_not_in_draft", f"Evidence is absent from draft: {evidence[:80]}"))

    for evidence in contract.get("required_evidence_in_draft", []) if isinstance(contract, dict) else []:
        if isinstance(evidence, str) and evidence.strip() and evidence.strip() not in draft:
            errors.append(issue("required_evidence_not_in_draft", f"Contract-required evidence is absent from draft: {evidence[:80]}"))

    for index, event in enumerate(card.get("events", []) or []):
        if not isinstance(event, dict):
            continue
        has_participants = any(isinstance(item, str) for item in event.get("participants", []) or [])
        has_location = isinstance(event.get("location"), str) and bool(event["location"].strip())
        evidence = event.get("evidence")
        if (has_participants or has_location) and not (isinstance(evidence, str) and evidence.strip()):
            errors.append(
                issue(
                    "event_projection_change_missing_evidence",
                    "Event with participants or location needs evidence because it mutates projections.",
                    path=f"events[{index}]",
                )
            )

    for collection_name in ("entity_changes", "knowledge_changes", "relationship_changes", "thread_events"):
        for index, item in enumerate(card.get(collection_name, []) or []):
            if isinstance(item, dict) and not item_has_evidence(item):
                errors.append(
                    issue(
                        f"{collection_name}_missing_evidence",
                        f"{collection_name} item needs evidence because it affects future writing.",
                        path=f"{collection_name}[{index}]",
                    )
                )

    for item in contract.get("must_satisfy", []) if isinstance(contract, dict) else []:
        if isinstance(item, str) and item.strip():
            if item not in draft and not contains_text(card, item):
                warnings.append(issue("contract_must_satisfy_not_exactly_traceable", f"Contract must_satisfy item is not exactly traceable in draft/card; EditorReview must have checked it: {item}"))

    allowed_thread = {
        move.get("thread_id"): move
        for move in contract.get("allowed_thread_moves", []) or []
        if isinstance(move, dict) and isinstance(move.get("thread_id"), str)
    }
    for event in card.get("thread_events", []) or []:
        if not isinstance(event, dict):
            continue
        thread_id = event.get("thread_id")
        to_state = event.get("to")
        if not isinstance(thread_id, str):
            errors.append(issue("thread_event_missing_thread_id", "Thread event lacks thread_id."))
            continue
        move = allowed_thread.get(thread_id)
        if move is None:
            errors.append(issue("thread_move_not_in_contract", f"Thread event not listed in contract: {thread_id}"))
        else:
            if isinstance(to_state, str) and to_state not in (move.get("allowed_to") or []):
                errors.append(issue("thread_move_not_allowed", f"Thread {thread_id} moves to {to_state}, not allowed by contract."))
            if isinstance(to_state, str) and to_state in (move.get("forbidden_to") or []):
                errors.append(issue("thread_move_forbidden", f"Thread {thread_id} moves to forbidden state {to_state}."))
        existing = threads.get(thread_id, {}) if isinstance(threads, dict) else {}
        previous_locks = set(existing.get("locked_until_reveal", []) or [])
        new_locks = set(event.get("still_locked", []) or [])
        removed = previous_locks - new_locks
        allowed_reveals = set(contract.get("allowed_reveals", []) or [])
        illegal_removed = [lock for lock in removed if lock not in allowed_reveals]
        if illegal_removed:
            errors.append(issue("lock_removed_without_reveal_permission", f"Thread {thread_id} removed locks without permission: {', '.join(illegal_removed)}"))

    bounds = contract.get("relationship_bounds", {}) if isinstance(contract.get("relationship_bounds"), dict) else {}
    for change in card.get("relationship_changes", []) or []:
        if not isinstance(change, dict):
            continue
        key = pair_key(change.get("pair"))
        to_state = change.get("to")
        if key is None or not isinstance(to_state, str):
            errors.append(issue("invalid_relationship_change", "Relationship change needs pair and to."))
            continue
        bound = bounds.get(key)
        if bound is None and isinstance(change.get("pair"), list):
            bound = bounds.get("__".join(reversed(change["pair"])))
        if bound is None:
            errors.append(issue("relationship_change_not_bounded", f"Relationship change has no contract bound: {key}"))
            continue
        if to_state in (bound.get("forbidden_moves") or []):
            errors.append(issue("relationship_move_forbidden", f"Relationship move forbidden: {to_state}"))
        if to_state not in (bound.get("allowed_moves") or []):
            errors.append(issue("relationship_move_not_allowed", f"Relationship move not allowed: {to_state}"))

    for index, item in enumerate(card.get("obligations_out", []) or []):
        if isinstance(item, dict) and not (isinstance(item.get("id"), str) and item["id"].strip()):
            errors.append(issue("obligation_id_missing", "Outgoing obligation needs a stable id.", path=f"obligations_out[{index}]"))
        if isinstance(item, dict):
            if not (isinstance(item.get("text"), str) and item["text"].strip()):
                errors.append(issue("obligation_text_missing", "Outgoing obligation needs text.", path=f"obligations_out[{index}]"))
            if item.get("mode") not in {"resolve_now", "maintain_pressure", "background", "avoid_contradiction"}:
                errors.append(issue("obligation_mode_invalid", "Outgoing obligation needs a valid mode.", path=f"obligations_out[{index}]"))
            if item.get("source_chapter") != args.chapter_id:
                errors.append(issue("obligation_source_chapter_invalid", "Outgoing obligation source_chapter must match target chapter.", path=f"obligations_out[{index}]"))

    resolved_ids = {
        item.get("id")
        for item in card.get("obligations_in", []) or []
        if isinstance(item, dict) and item.get("status") in {"resolved", "superseded"} and isinstance(item.get("id"), str)
    }
    resolved_texts = {
        item.get("text")
        for item in card.get("obligations_in", []) or []
        if isinstance(item, dict) and item.get("status") in {"resolved", "superseded"}
    }
    outgoing_ids = {
        item.get("id")
        for item in card.get("obligations_out", []) or []
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    outgoing = card.get("obligations_out", [])
    for obligation in obligations if isinstance(obligations, list) else []:
        if not isinstance(obligation, dict) or obligation.get("mode") != "resolve_now":
            continue
        obligation_id = obligation.get("id")
        text = obligation.get("text")
        if isinstance(obligation_id, str) and obligation_id.strip():
            if obligation_id not in resolved_ids and obligation_id not in outgoing_ids:
                errors.append(issue("resolve_now_obligation_unsettled", f"Resolve-now obligation not settled by card id: {obligation_id}"))
        elif isinstance(text, str) and text.strip():
            if text not in resolved_texts and not contains_text(outgoing, text):
                errors.append(issue("resolve_now_obligation_unsettled", f"Resolve-now obligation not settled by card: {text}"))

    for obligation in obligations if isinstance(obligations, list) else []:
        if not isinstance(obligation, dict) or obligation.get("mode") != "avoid_contradiction":
            continue
        obligation_id = obligation.get("id")
        text = obligation.get("text")
        if isinstance(obligation_id, str) and obligation_id.strip() and obligation_id in resolved_ids:
            errors.append(issue("avoid_contradiction_obligation_resolved", f"Avoid-contradiction obligation should not be resolved by card id: {obligation_id}"))
        elif isinstance(text, str) and text.strip() and text in resolved_texts:
            errors.append(issue("avoid_contradiction_obligation_resolved", f"Avoid-contradiction obligation should not be resolved by card: {text}"))

    result = {
        "schema_version": 1,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "evidence_count": len(evidence_values(card)),
            "thread_events": len(card.get("thread_events", []) or []),
            "relationship_changes": len(card.get("relationship_changes", []) or []),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
