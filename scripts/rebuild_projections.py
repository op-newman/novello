#!/usr/bin/env python3
"""Replay Novello chapter cards into generated projections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import force_utf8_stdio, issue, load_cards, write_json


def pair_key(pair: list[str]) -> str:
    return "__".join(pair)


def ensure_thread(threads: dict[str, Any], thread_id: str) -> dict[str, Any]:
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


def rebuild(project_root: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    entities: dict[str, Any] = {}
    relationships: dict[str, Any] = {}
    threads: dict[str, Any] = {}
    obligations: list[dict[str, Any]] = []
    reader_memory: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    cards, source_errors = load_cards(project_root)
    errors.extend(source_errors)

    for card in cards:
        raw_chapter_id = card.get("chapter_id")
        if not isinstance(raw_chapter_id, int) or raw_chapter_id <= 0:
            continue
        chapter_id = raw_chapter_id

        for event in card.get("events", []) or []:
            if not isinstance(event, dict):
                continue
            for entity_id in event.get("participants", []) or []:
                if not isinstance(entity_id, str):
                    continue
                state = entities.setdefault(entity_id, {"id": entity_id})
                state["last_seen_chapter"] = chapter_id
                if isinstance(event.get("location"), str):
                    state["current_location"] = event["location"]
            if isinstance(event.get("text"), str):
                reader_memory.append({"chapter_id": chapter_id, "kind": "event", "text": event["text"]})

        for change in card.get("entity_changes", []) or []:
            if not isinstance(change, dict):
                continue
            entity_id = change.get("entity_id")
            if not isinstance(entity_id, str):
                errors.append(issue("entity_change_missing_entity_id", "Entity change lacks entity_id."))
                continue
            state = entities.setdefault(entity_id, {"id": entity_id})
            state["last_seen_chapter"] = chapter_id
            updates = change.get("set") or {}
            if isinstance(updates, dict):
                for field, value in updates.items():
                    state[field] = value

        for change in card.get("knowledge_changes", []) or []:
            if not isinstance(change, dict):
                continue
            character_id = change.get("character_id")
            fact = change.get("fact")
            status = change.get("status")
            if not all(isinstance(value, str) for value in (character_id, fact, status)):
                errors.append(issue("invalid_knowledge_change", "Knowledge change needs character_id, fact, and status."))
                continue
            state = entities.setdefault(character_id, {"id": character_id})
            state.setdefault("knowledge", {})
            state["knowledge"][fact] = {"status": status, "chapter_id": chapter_id}
            state["last_seen_chapter"] = chapter_id

        for change in card.get("relationship_changes", []) or []:
            if not isinstance(change, dict):
                continue
            pair = change.get("pair")
            to_state = change.get("to")
            if not (isinstance(pair, list) and len(pair) == 2 and isinstance(to_state, str)):
                errors.append(issue("invalid_relationship_change", "Relationship change needs pair[2] and to."))
                continue
            relationships[pair_key(pair)] = {"pair": pair, "phase": to_state, "last_changed_chapter": chapter_id}

        for event in card.get("thread_events", []) or []:
            if not isinstance(event, dict):
                continue
            thread_id = event.get("thread_id")
            if not isinstance(thread_id, str):
                errors.append(issue("thread_event_missing_thread_id", "Thread event lacks thread_id."))
                continue
            thread = ensure_thread(threads, thread_id)
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

        for lock in card.get("locks_asserted", []) or []:
            if isinstance(lock, str):
                reader_memory.append({"chapter_id": chapter_id, "kind": "lock", "text": lock})

    projection = {
        "entities": entities,
        "relationships": relationships,
        "threads": threads,
        "obligations": obligations,
        "reader_memory": reader_memory[-200:],
    }
    return projection, errors


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root)
    projection, errors = rebuild(project_root)
    if args.write:
        write_json(project_root / "projections" / "entities.current.json", projection["entities"])
        write_json(project_root / "projections" / "relationships.current.json", projection["relationships"])
        write_json(project_root / "projections" / "threads.current.json", projection["threads"])
        write_json(project_root / "projections" / "obligations.open.json", projection["obligations"])
        write_json(project_root / "projections" / "reader_memory.current.json", projection["reader_memory"])

    result = {
        "schema_version": 1,
        "passed": not errors,
        "errors": errors,
        "stats": {
            "entities": len(projection["entities"]),
            "relationships": len(projection["relationships"]),
            "threads": len(projection["threads"]),
            "open_obligations": len(projection["obligations"]),
            "reader_memory": len(projection["reader_memory"]),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
