#!/usr/bin/env python3
"""Generate a conservative Novello chapter plan draft from projections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import chapter_digits, force_utf8_stdio, issue, padded, read_json, write_json


def text_of(value: Any, fallback: str = "") -> str:
    return value if isinstance(value, str) and value.strip() else fallback


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def find_arc(global_plan: dict[str, Any], chapter_id: int) -> dict[str, Any]:
    for arc in as_list(global_plan.get("major_arcs")):
        if not isinstance(arc, dict):
            continue
        raw = arc.get("chapters")
        if not isinstance(raw, str) or "-" not in raw:
            continue
        start_raw, end_raw = raw.split("-", 1)
        try:
            start = int(start_raw.strip())
            end = int(end_raw.strip())
        except ValueError:
            continue
        if start <= chapter_id <= end:
            return arc
    return {}


def due_obligations(obligations: list[Any], chapter_id: int) -> list[dict[str, Any]]:
    due: list[dict[str, Any]] = []
    for item in obligations:
        if not isinstance(item, dict):
            continue
        mode = item.get("mode")
        due_chapter = item.get("due_chapter")
        if mode == "resolve_now" or (isinstance(due_chapter, int) and due_chapter <= chapter_id):
            due.append(item)
    return due


def due_threads(threads: dict[str, Any], chapter_id: int) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for thread_id, item in threads.items():
        if not isinstance(item, dict):
            continue
        next_review = item.get("next_review_chapter")
        priority = item.get("priority")
        if priority == "high" and isinstance(next_review, int) and next_review <= chapter_id:
            found.append({"thread_id": thread_id, **item})
    return found


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--chapter-id", type=int, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root)
    pad = padded(args.chapter_id, chapter_digits(project_root))
    plan_path = project_root / "plans" / "chapters" / f"{pad}.json"
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if plan_path.exists() and not args.overwrite:
        errors.append(issue("plan_already_exists", "Chapter plan already exists; use --overwrite to replace.", path=str(plan_path)))

    global_plan = read_json(project_root / "plans" / "global_plan.json", default={})
    arc = find_arc(global_plan if isinstance(global_plan, dict) else {}, args.chapter_id)
    threads = read_json(project_root / "projections" / "threads.current.json", default={})
    obligations = read_json(project_root / "projections" / "obligations.open.json", default=[])

    due = due_obligations(obligations if isinstance(obligations, list) else [], args.chapter_id)
    review_threads = due_threads(threads if isinstance(threads, dict) else {}, args.chapter_id)

    goals: list[str] = []
    for item in due:
        obligation_text = text_of(item.get("text"), text_of(item.get("id"), "Settle due obligation."))
        goals.append(f"Settle due obligation: {obligation_text}")
    for item in review_threads:
        state = text_of(item.get("current_state"), text_of(item.get("state"), "current state unclear"))
        goals.append(f"Review high-priority thread {item['thread_id']} from state {state}.")
    if not goals:
        arc_promise = text_of(arc.get("promise") if isinstance(arc, dict) else None, "Advance the current arc without resolving it too quickly.")
        goals.append(f"Advance arc pressure: {arc_promise}")

    planned_threads = []
    seen_threads: set[str] = set()
    for item in review_threads:
        thread_id = item.get("thread_id")
        if isinstance(thread_id, str) and thread_id not in seen_threads:
            planned_threads.append(thread_id)
            seen_threads.add(thread_id)
    for item in due:
        text = json.dumps(item, ensure_ascii=False)
        for thread_id in (threads.keys() if isinstance(threads, dict) else []):
            if isinstance(thread_id, str) and thread_id in text and thread_id not in seen_threads:
                planned_threads.append(thread_id)
                seen_threads.add(thread_id)

    locked = []
    for item in (threads.values() if isinstance(threads, dict) else []):
        if not isinstance(item, dict):
            continue
        for lock in as_list(item.get("locked_until_reveal")):
            if isinstance(lock, str) and lock not in locked:
                locked.append(lock)

    title = "Next Step"
    if due:
        title = "Settle Promise"
    elif review_threads:
        title = "Pressure Review"

    plan = {
        "schema_version": 1,
        "chapter_id": args.chapter_id,
        "title": title,
        "goals": goals[:6],
        "required_reveals": [],
        "forbidden_reveals": locked,
        "plot_threads_advanced": planned_threads[:6],
        "ending_hook": "End with a concrete next pressure or next action, not a full resolution.",
        "scenes": [
            {
                "id": "scene:001_due_pressure",
                "purpose": "Pay off due obligations and touch overdue high-priority threads.",
                "location": "choose from active projections",
            },
            {
                "id": "scene:002_consequence",
                "purpose": "Show the cost, obstacle, or reader-visible consequence of the action.",
                "location": "choose from active projections",
            },
        ],
        "style_notes": [
            "Draft plan generated by script; main agent must refine before writing if it is too generic.",
            "Do not resolve arc pressure too quickly.",
        ],
        "target_length": "3000-3800 Chinese characters",
        "generator_notes": {
            "arc_id": arc.get("id") if isinstance(arc, dict) else None,
            "due_obligation_ids": [item.get("id") for item in due if isinstance(item.get("id"), str)],
            "due_thread_ids": [item.get("thread_id") for item in review_threads],
        },
    }

    if args.write and not errors:
        write_json(plan_path, plan)

    result = {
        "schema_version": 1,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "wrote_plan": bool(args.write and not errors),
        "path": str(plan_path),
        "plan": plan,
        "stats": {
            "goals": len(plan["goals"]),
            "due_obligations": len(due),
            "due_threads": len(review_threads),
            "forbidden_reveals": len(locked),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
