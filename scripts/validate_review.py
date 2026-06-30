#!/usr/bin/env python3
"""Validate the lightweight Novello review / RetconScan structure."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import chapter_digits, force_utf8_stdio, issue, padded


RETCON_FIELDS = [
    "durable_new_fact",
    "knowledge_leak",
    "relationship_jump",
    "obligation_change",
    "new_reader_promise",
]
RETCON_VALUES = {"none", "suspected", "found", "pass"}
RETCON_RISK_VALUES = {"suspected", "found"}


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--chapter-id", type=int, required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root)
    pad = padded(args.chapter_id, chapter_digits(project_root))
    review_path = project_root / "reviews" / f"{pad}.md"
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    try:
        review = review_path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        review = ""
        errors.append(issue("review_missing", "Review file is missing.", path=str(review_path)))

    if review:
        for heading in ("## Verdict", "## Issues", "## Contract Experience", "## Notes", "## RetconScan"):
            if heading not in review:
                errors.append(issue("review_section_missing", f"Review missing section: {heading}", path=str(review_path)))

        verdict_match = re.search(r"## Verdict\s+([a-zA-Z_|-]+)", review)
        if not verdict_match:
            errors.append(issue("review_verdict_missing", "Review verdict is missing.", path=str(review_path)))
            review_verdict = None
        elif verdict_match.group(1).strip() not in {"pass", "revise", "halt"}:
            errors.append(issue("review_verdict_invalid", "Review verdict must be pass, revise, or halt.", path=str(review_path)))
            review_verdict = None
        else:
            review_verdict = verdict_match.group(1).strip()

        retcon_values_found: dict[str, str] = {}
        for field in RETCON_FIELDS:
            pattern = rf"-\s*{re.escape(field)}:\s*([a-zA-Z_]+)\s*-"
            match = re.search(pattern, review)
            if not match:
                errors.append(issue("retcon_field_missing", f"RetconScan missing field: {field}", path=str(review_path)))
                continue
            value = match.group(1).strip()
            if value not in RETCON_VALUES:
                errors.append(issue("retcon_field_invalid", f"RetconScan field {field} has invalid value: {value}", path=str(review_path)))
            retcon_values_found[field] = value

        verdict_match = re.search(r"retcon_verdict:\s*([a-zA-Z_]+)", review)
        if not verdict_match:
            errors.append(issue("retcon_verdict_missing", "RetconScan verdict is missing.", path=str(review_path)))
            retcon_verdict = None
        elif verdict_match.group(1).strip() not in {"pass", "revise", "halt"}:
            errors.append(issue("retcon_verdict_invalid", "RetconScan verdict must be pass, revise, or halt.", path=str(review_path)))
            retcon_verdict = None
        else:
            retcon_verdict = verdict_match.group(1).strip()

        if retcon_verdict == "pass":
            found = [field for field, value in retcon_values_found.items() if value == "found"]
            suspected = [field for field, value in retcon_values_found.items() if value == "suspected"]
            if found:
                errors.append(
                    issue(
                        "retcon_pass_with_found_issue",
                        f"RetconScan cannot pass with found fields: {', '.join(found)}",
                        path=str(review_path),
                    )
                )
            elif suspected:
                warnings.append(
                    issue(
                        "retcon_pass_with_suspected_issue",
                        f"RetconScan passed with suspected fields; log degraded assumptions or revise: {', '.join(suspected)}",
                        path=str(review_path),
                    )
                )

        if review_verdict == "pass" and re.search(r"-\s*severity:\s*(blocker|high)\b", review):
            errors.append(issue("review_pass_with_high_issue", "Review cannot pass with high/blocker issue present.", path=str(review_path)))

        if review_verdict == "pass" and retcon_verdict in {"revise", "halt"}:
            errors.append(
                issue(
                    "review_pass_with_failed_retcon",
                    f"Review verdict cannot be pass when RetconScan verdict is {retcon_verdict}.",
                    path=str(review_path),
                )
            )

        if "## Adversarial Findings" in review:
            adversarial = review.split("## Adversarial Findings", 1)[1].split("## RetconScan", 1)[0]
            adv_match = re.search(r"(?m)^verdict:\s*([a-zA-Z_]+)\s*$", adversarial)
            if not adv_match:
                errors.append(issue("adversarial_verdict_missing", "Adversarial findings are present without a verdict line.", path=str(review_path)))
            elif adv_match.group(1).strip() not in {"pass", "revise", "halt"}:
                errors.append(issue("adversarial_verdict_invalid", "Adversarial verdict must be pass, revise, or halt.", path=str(review_path)))

    result = {
        "schema_version": 1,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {"review_chars": len(review)},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
