#!/usr/bin/env python3
"""Validate a Novello chapter card against contract, projection, and draft."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import DuplicateKeyError, chapter_digits, force_utf8_stdio, issue, padded, read_json


def evidence_pool(card: dict[str, Any], errors: list[dict[str, str]], warnings: list[dict[str, str]], draft: str) -> dict[str, str]:
    raw_pool = card.get("evidence", [])
    pool: dict[str, str] = {}
    if raw_pool is None:
        errors.append(issue("evidence_pool_invalid", "Card evidence must be a list when present."))
        return pool
    if not isinstance(raw_pool, list):
        errors.append(issue("evidence_pool_invalid", "Card evidence must be a list when present."))
        return pool
    for index, item in enumerate(raw_pool):
        if not isinstance(item, dict):
            errors.append(issue("evidence_item_invalid", "Evidence pool item must be an object.", path=f"evidence[{index}]"))
            continue
        evidence_id = item.get("id")
        quote = item.get("quote")
        if not (isinstance(evidence_id, str) and evidence_id.strip()):
            errors.append(issue("evidence_id_missing", "Evidence pool item needs a non-empty id.", path=f"evidence[{index}]"))
            continue
        evidence_id = evidence_id.strip()
        if evidence_id in pool:
            errors.append(issue("evidence_id_duplicate", f"Duplicate evidence id: {evidence_id}", path=f"evidence[{index}]"))
            continue
        if not (isinstance(quote, str) and quote.strip()):
            errors.append(issue("evidence_quote_missing", f"Evidence item {evidence_id} needs a non-empty quote.", path=f"evidence[{index}]"))
            continue
        quote = quote.strip()
        pool[evidence_id] = quote
        if quote not in draft:
            errors.append(issue("evidence_not_in_draft", f"Evidence quote is absent from draft: {quote[:80]}", path=f"evidence[{index}]"))
        for field in item:
            if field not in {"id", "quote"}:
                warnings.append(issue("evidence_unknown_field", f"Unknown evidence field ignored: {field}", path=f"evidence[{index}]"))
    return pool


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


def item_evidence_quote(
    item: Any,
    *,
    pool: dict[str, str],
    errors: list[dict[str, str]],
    path: str,
    ref_field: str = "evidence_ref",
    required: bool = True,
) -> str | None:
    if not isinstance(item, dict):
        return None
    ref = item.get(ref_field)
    if isinstance(ref, str) and ref.strip():
        ref = ref.strip()
        if ref not in pool:
            errors.append(issue("evidence_ref_missing", f"{ref_field} points to missing evidence id: {ref}", path=path))
            return None
        return pool[ref]
    if required:
        errors.append(issue("evidence_ref_missing", f"Item needs {ref_field}.", path=path))
    return None


def list_len(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def int_config(config: Any, key: str, default: int) -> int:
    if isinstance(config, dict) and isinstance(config.get(key), int) and config[key] > 0:
        return config[key]
    return default


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
    except DuplicateKeyError as exc:
        card = {}
        errors.append(issue("card_json_duplicate_key", f"Card JSON has duplicate key: {exc.key}", path=str(card_path)))
    except FileNotFoundError:
        card = {}
        errors.append(issue("card_missing", "Card file is missing.", path=str(card_path)))
    try:
        contract = read_json(contract_path)
    except DuplicateKeyError as exc:
        contract = {}
        errors.append(issue("contract_json_duplicate_key", f"Contract JSON has duplicate key: {exc.key}", path=str(contract_path)))
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
    relationships_proj = read_json(project_root / "projections" / "relationships.current.json", default={})
    config = read_json(project_root / "novello.json", default={})

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
    if isinstance(card, dict) and "evidence" not in card:
        errors.append(issue("evidence_pool_missing", "Cards must include top-level evidence[].", path=str(card_path)))

    pool = evidence_pool(card, errors, warnings, draft) if isinstance(card, dict) else {}

    for evidence in contract.get("required_evidence_in_draft", []) if isinstance(contract, dict) else []:
        if isinstance(evidence, str) and evidence.strip() and evidence.strip() not in draft:
            errors.append(issue("required_evidence_not_in_draft", f"Contract-required evidence is absent from draft: {evidence[:80]}"))

    for index, event in enumerate(card.get("events", []) or []):
        if not isinstance(event, dict):
            continue
        has_participants = any(isinstance(item, str) for item in event.get("participants", []) or [])
        has_location = isinstance(event.get("location"), str) and bool(event["location"].strip())
        if has_participants or has_location:
            evidence = item_evidence_quote(
                event,
                pool=pool,
                errors=errors,
                path=f"events[{index}]",
            )
            if evidence is None:
                errors.append(
                    issue(
                        "event_projection_change_missing_evidence",
                        "Event with participants or location needs evidence because it mutates projections.",
                        path=f"events[{index}]",
                    )
                )
            elif evidence not in draft:
                errors.append(issue("evidence_not_in_draft", f"Evidence is absent from draft: {evidence[:80]}", path=f"events[{index}]"))

    for collection_name in ("entity_changes", "knowledge_changes", "relationship_changes", "thread_events"):
        for index, item in enumerate(card.get(collection_name, []) or []):
            if not isinstance(item, dict):
                continue
            evidence = item_evidence_quote(
                item,
                pool=pool,
                errors=errors,
                path=f"{collection_name}[{index}]",
            )
            if evidence is None:
                errors.append(
                    issue(
                        f"{collection_name}_missing_evidence",
                        f"{collection_name} item needs evidence because it affects future writing.",
                        path=f"{collection_name}[{index}]",
                    )
                )
            elif evidence not in draft:
                errors.append(issue("evidence_not_in_draft", f"Evidence is absent from draft: {evidence[:80]}", path=f"{collection_name}[{index}]"))

    for index, item in enumerate(card.get("obligations_in", []) or []):
        if isinstance(item, dict) and item.get("status") in {"resolved", "superseded"}:
            evidence = item_evidence_quote(
                item,
                pool=pool,
                errors=errors,
                path=f"obligations_in[{index}]",
            )
            if evidence is None:
                errors.append(
                    issue(
                        "obligation_resolution_missing_evidence",
                        "Resolved or superseded obligation needs evidence because it changes future writing state.",
                        path=f"obligations_in[{index}]",
                    )
                )
            elif evidence not in draft:
                errors.append(issue("evidence_not_in_draft", f"Evidence is absent from draft: {evidence[:80]}", path=f"obligations_in[{index}]"))

    semantic_review_items = 0
    for item in contract.get("must_satisfy", []) if isinstance(contract, dict) else []:
        if isinstance(item, str) and item.strip():
            if item not in draft and not contains_text(card, item):
                semantic_review_items += 1

    knowledge_locks = set(contract.get("knowledge_locks", []) or []) if isinstance(contract, dict) else set()
    allowed_reveals = set(contract.get("allowed_reveals", []) or []) if isinstance(contract, dict) else set()

    # A locked fact may not become confirmed knowledge unless the contract reveals it.
    # "suspected" keeps the fact unconfirmed and stays within the lock.
    for index, change in enumerate(card.get("knowledge_changes", []) or []):
        if not isinstance(change, dict):
            continue
        fact = change.get("fact")
        if change.get("status") == "known" and isinstance(fact, str) and fact in knowledge_locks and fact not in allowed_reveals:
            errors.append(
                issue(
                    "knowledge_lock_violated",
                    f"Character confirms a locked fact without contract reveal permission: {fact}",
                    path=f"knowledge_changes[{index}]",
                )
            )

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
        illegal_removed = [lock for lock in removed if lock not in allowed_reveals]
        if illegal_removed:
            errors.append(issue("lock_removed_without_reveal_permission", f"Thread {thread_id} removed locks without permission: {', '.join(illegal_removed)}"))

    bounds = contract.get("relationship_bounds", {}) if isinstance(contract.get("relationship_bounds"), dict) else {}
    for index, change in enumerate(card.get("relationship_changes", []) or []):
        if not isinstance(change, dict):
            continue
        key = pair_key(change.get("pair"))

        if change.get("type") == "relationship_beat":
            if key is None:
                errors.append(issue("invalid_relationship_beat", "Relationship beat needs a valid pair of two character ids.", path=f"relationship_changes[{index}]"))
                continue
            if isinstance(change.get("to"), str) and change["to"].strip():
                errors.append(issue("relationship_beat_has_transition", "Relationship beat must not assert a phase transition 'to'; use a normal relationship change for that.", path=f"relationship_changes[{index}]"))
            current_phase = change.get("current_phase")
            if not (isinstance(current_phase, str) and current_phase.strip()):
                errors.append(issue("relationship_beat_missing_current_phase", "Relationship beat needs a current_phase string.", path=f"relationship_changes[{index}]"))
            else:
                proj = relationships_proj.get(key) if isinstance(relationships_proj, dict) else None
                if proj is None and isinstance(relationships_proj, dict) and isinstance(change.get("pair"), list):
                    proj = relationships_proj.get("__".join(reversed(change["pair"])))
                if isinstance(proj, dict):
                    proj_phase = proj.get("phase")
                    if isinstance(proj_phase, str) and proj_phase.strip() and proj_phase != current_phase:
                        errors.append(
                            issue(
                                "relationship_beat_phase_mismatch",
                                f"Relationship beat current_phase {current_phase!r} does not match projection phase {proj_phase!r} for {key}.",
                                path=f"relationship_changes[{index}]",
                            )
                        )
            # A beat may not push toward a phase the contract forbids. Match the
            # forbidden phase name as a substring of the beat's direction (e.g.
            # direction "toward_formal_love" is blocked when "formal_love" is
            # forbidden). Only the contract blacklist is enforced; a beat toward a
            # distant-but-legal phase is allowed.
            beat_bound = bounds.get(key)
            if beat_bound is None and isinstance(change.get("pair"), list):
                beat_bound = bounds.get("__".join(reversed(change["pair"])))
            direction = change.get("direction")
            if not (isinstance(direction, str) and direction.strip()):
                errors.append(issue("relationship_beat_missing_direction", "Relationship beat needs a direction string.", path=f"relationship_changes[{index}]"))
            elif beat_bound is None:
                errors.append(issue("relationship_beat_not_bounded", f"Relationship beat has no contract bound: {key}", path=f"relationship_changes[{index}]"))
            elif isinstance(beat_bound, dict):
                allowed_beats = beat_bound.get("allowed_relationship_beats")
                if isinstance(allowed_beats, list):
                    allowed = [item.strip() for item in allowed_beats if isinstance(item, str) and item.strip()]
                    if allowed and direction.strip() not in allowed:
                        errors.append(
                            issue(
                                "relationship_beat_not_allowed",
                                f"Relationship beat direction is not allowed by contract for {key}: {direction}",
                                path=f"relationship_changes[{index}]",
                            )
                        )
                for forbidden in beat_bound.get("forbidden_moves") or []:
                    if isinstance(forbidden, str) and forbidden and forbidden in direction:
                        errors.append(
                            issue(
                                "relationship_beat_direction_forbidden",
                                f"Relationship beat pushes toward a forbidden move for {key}: {forbidden}",
                                path=f"relationship_changes[{index}]",
                            )
                        )
                        break
            continue

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
            obligation_type = item.get("type")
            if obligation_type is not None and not (isinstance(obligation_type, str) and obligation_type.strip()):
                errors.append(issue("obligation_type_invalid", "Outgoing obligation type, when present, must be a non-empty string.", path=f"obligations_out[{index}]"))
            due_chapter = item.get("due_chapter")
            if due_chapter is not None and not isinstance(due_chapter, int):
                errors.append(issue("obligation_due_chapter_invalid", "Outgoing obligation due_chapter, when present, must be an integer.", path=f"obligations_out[{index}]"))
            elif isinstance(due_chapter, int) and due_chapter <= args.chapter_id:
                errors.append(issue("obligation_due_chapter_not_future", "Outgoing obligation due_chapter must be later than its source chapter.", path=f"obligations_out[{index}]"))
            if obligation_type == "reader_promise":
                planted_evidence = item_evidence_quote(
                    item,
                    pool=pool,
                    errors=errors,
                    path=f"obligations_out[{index}]",
                    ref_field="planted_evidence_ref",
                )
                if planted_evidence is None:
                    errors.append(issue("reader_promise_missing_planted_evidence", "A reader_promise obligation needs planted_evidence_ref.", path=f"obligations_out[{index}]"))
                elif planted_evidence not in draft:
                    errors.append(issue("reader_promise_planted_evidence_not_in_draft", "reader_promise planted evidence must be quoted from the draft.", path=f"obligations_out[{index}]"))
                conditions = item.get("fulfillment_conditions")
                if not (isinstance(conditions, list) and any(isinstance(c, str) and c.strip() for c in conditions)):
                    errors.append(issue("reader_promise_missing_fulfillment_conditions", "A reader_promise obligation needs at least one fulfillment condition.", path=f"obligations_out[{index}]"))
            else:
                conditions = item.get("fulfillment_conditions")
                if conditions is not None and not isinstance(conditions, list):
                    errors.append(issue("obligation_fulfillment_conditions_invalid", "Outgoing obligation fulfillment_conditions, when present, must be a list.", path=f"obligations_out[{index}]"))

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
        if not isinstance(obligation, dict):
            continue
        mode = obligation.get("mode")
        obligation_id = obligation.get("id")
        text = obligation.get("text")
        has_id = isinstance(obligation_id, str) and bool(obligation_id.strip())
        has_text = isinstance(text, str) and bool(text.strip())
        ref = obligation_id if has_id else (text if has_text else None)

        # An obligation is "resolved" only when the card marks it resolved/superseded.
        # It is "settled" when resolved or carried forward as a new outgoing obligation.
        if has_id:
            resolved = obligation_id in resolved_ids
            settled = resolved or obligation_id in outgoing_ids
        elif has_text:
            resolved = text in resolved_texts
            settled = resolved or contains_text(outgoing, text)
        else:
            resolved = settled = False

        due_chapter = obligation.get("due_chapter")
        is_due = isinstance(due_chapter, int) and due_chapter <= args.chapter_id

        if mode == "resolve_now":
            if ref is not None and not settled:
                errors.append(issue("resolve_now_obligation_unsettled", f"Resolve-now obligation not settled by card: {ref}"))
        elif mode == "avoid_contradiction":
            if ref is not None and resolved:
                errors.append(issue("avoid_contradiction_obligation_resolved", f"Avoid-contradiction obligation should not be resolved by card: {ref}"))
        elif is_due:
            if ref is not None and not settled:
                errors.append(issue("due_obligation_unsettled", f"Obligation past its due_chapter is not settled by card: {ref}"))

    card_chars = len(json.dumps(card, ensure_ascii=False))
    evidence_count = len(pool)
    event_count = list_len(card.get("events"))
    entity_change_count = list_len(card.get("entity_changes"))
    knowledge_change_count = list_len(card.get("knowledge_changes"))
    relationship_change_count = list_len(card.get("relationship_changes"))
    thread_event_count = list_len(card.get("thread_events"))
    obligation_in_count = list_len(card.get("obligations_in"))
    obligation_out_count = list_len(card.get("obligations_out"))
    projection_item_count = (
        event_count
        + entity_change_count
        + knowledge_change_count
        + relationship_change_count
        + thread_event_count
        + obligation_in_count
        + obligation_out_count
    )

    card_soft_budget = int_config(config, "card_soft_budget_chars", 5500)
    item_soft_budget = int_config(config, "card_soft_projection_items", 22)
    evidence_soft_budget = int_config(config, "card_soft_evidence_items", 24)
    if card_chars > card_soft_budget:
        warnings.append(issue("card_over_soft_budget", f"Card has {card_chars} chars, over soft budget {card_soft_budget}. Keep cards receipt-like.", path=str(card_path)))
    if projection_item_count > item_soft_budget:
        warnings.append(issue("card_many_projection_items", f"Card has {projection_item_count} projection-relevant items, over soft budget {item_soft_budget}.", path=str(card_path)))
    if evidence_count > evidence_soft_budget:
        warnings.append(issue("card_many_evidence_items", f"Card has {evidence_count} evidence snippets, over soft budget {evidence_soft_budget}.", path=str(card_path)))

    result = {
        "schema_version": 1,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "card_chars": card_chars,
            "evidence_count": evidence_count,
            "events": event_count,
            "entity_changes": entity_change_count,
            "knowledge_changes": knowledge_change_count,
            "thread_events": thread_event_count,
            "relationship_changes": relationship_change_count,
            "obligations_in": obligation_in_count,
            "obligations_out": obligation_out_count,
            "projection_items": projection_item_count,
            "semantic_must_satisfy_review_items": semantic_review_items,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
