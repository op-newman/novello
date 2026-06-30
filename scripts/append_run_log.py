#!/usr/bin/env python3
"""Append a completed Novello run log record from validator reports."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from common import DuplicateKeyError, chapter_digits, force_utf8_stdio, issue, padded, read_json


def load_report(path: str | None, default: dict[str, Any]) -> dict[str, Any]:
    if not path:
        return default
    value = read_json(Path(path))
    return value if isinstance(value, dict) else default


def require_passed_report(name: str, path: str | None, report: dict[str, Any], errors: list[dict[str, str]]) -> None:
    if not path:
        errors.append(issue(f"{name}_report_missing", f"{name} report path is required before appending a completed run log."))
        return
    if report.get("passed") is not True:
        errors.append(issue(f"{name}_report_not_passed", f"{name} report must have passed: true."))


def read_review_verdict(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return "missing"
    marker = "## Verdict"
    if marker not in text:
        return "unknown"
    after = text.split(marker, 1)[1].strip().splitlines()
    return after[0].strip() if after else "unknown"


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--chapter-id", type=int, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--packet-report")
    parser.add_argument("--card-report")
    parser.add_argument("--projection-report")
    parser.add_argument("--writer-revisions", type=int, default=0)
    parser.add_argument("--writer-new-fact", action="append", default=[])
    parser.add_argument("--degraded-assumption", action="append", default=[])
    args = parser.parse_args()

    project_root = Path(args.project_root)
    pad = padded(args.chapter_id, chapter_digits(project_root))
    run_id = args.run_id or f"{datetime.now().strftime('%Y%m%dT%H%M%S')}_ch{args.chapter_id}"
    errors: list[dict[str, str]] = []

    try:
        packet_report = load_report(args.packet_report, {"passed": None, "errors": [], "warnings": [], "stats": {}})
        card_report = load_report(args.card_report, {"passed": None, "errors": [], "warnings": [], "stats": {}})
        projection_report = load_report(args.projection_report, {"passed": None, "errors": [], "stats": {}})
    except DuplicateKeyError as exc:
        errors.append(issue("report_json_duplicate_key", f"Report JSON has duplicate key: {exc.key}"))
        packet_report = {"passed": None, "errors": [], "warnings": [], "stats": {}}
        card_report = {"passed": None, "errors": [], "warnings": [], "stats": {}}
        projection_report = {"passed": None, "errors": [], "stats": {}}
    except FileNotFoundError as exc:
        errors.append(issue("report_missing", f"Report file is missing: {exc.filename}"))
        packet_report = {"passed": None, "errors": [], "warnings": [], "stats": {}}
        card_report = {"passed": None, "errors": [], "warnings": [], "stats": {}}
        projection_report = {"passed": None, "errors": [], "stats": {}}
    except json.JSONDecodeError as exc:
        errors.append(issue("report_json_invalid", f"Report JSON is invalid: {exc}"))
        packet_report = {"passed": None, "errors": [], "warnings": [], "stats": {}}
        card_report = {"passed": None, "errors": [], "warnings": [], "stats": {}}
        projection_report = {"passed": None, "errors": [], "stats": {}}

    required_files = [
        project_root / "contracts" / f"{pad}.json",
        project_root / "packets" / f"{pad}.json",
        project_root / "chapters" / f"{pad}.md",
        project_root / "reviews" / f"{pad}.md",
        project_root / "cards" / f"{pad}.json",
    ]
    files_committed = []
    for path in required_files:
        rel = path.relative_to(project_root).as_posix()
        if path.exists() and path.stat().st_size > 0:
            files_committed.append(rel)
        else:
            errors.append(issue("run_log_required_file_missing", f"Required file is missing or empty: {rel}", path=str(path)))

    require_passed_report("packet", args.packet_report, packet_report, errors)
    require_passed_report("card", args.card_report, card_report, errors)
    require_passed_report("projection", args.projection_report, projection_report, errors)

    review_path = project_root / "reviews" / f"{pad}.md"
    review_verdict = read_review_verdict(review_path)
    if review_verdict != "pass":
        errors.append(issue("review_verdict_not_passed", f"Review verdict must be pass before appending a completed run log: {review_verdict}", path=str(review_path)))

    if errors:
        result = {"schema_version": 1, "passed": False, "errors": errors, "warnings": [], "appended": False}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    record = {
        "schema_version": 1,
        "status": "completed",
        "chapter_id": args.chapter_id,
        "run_id": run_id,
        "contract": {"path": f"contracts/{pad}.json", "generated": True, "halted_reasons": []},
        "packet_validation": {
            "passed": packet_report.get("passed"),
            "errors": packet_report.get("errors", []),
            "warnings": packet_report.get("warnings", []),
            "stats": packet_report.get("stats", {}),
        },
        "writer": {"revision_count": args.writer_revisions, "new_facts": args.writer_new_fact},
        "editor_review": {"path": f"reviews/{pad}.md", "verdict": review_verdict, "issues": []},
        "card_validation": {
            "passed": card_report.get("passed"),
            "errors": card_report.get("errors", []),
            "warnings": card_report.get("warnings", []),
            "stats": card_report.get("stats", {}),
        },
        "projection_rebuild": {
            "passed": projection_report.get("passed"),
            "errors": projection_report.get("errors", []),
            "stats": projection_report.get("stats", {}),
        },
        "files_committed": files_committed,
        "degraded_assumptions": args.degraded_assumption,
    }

    log_path = project_root / "logs" / "runs.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    result = {"schema_version": 1, "passed": True, "errors": [], "warnings": [], "appended": True, "run_id": run_id}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
