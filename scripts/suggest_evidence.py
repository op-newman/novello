#!/usr/bin/env python3
"""Suggest exact draft evidence snippets for Novello cards."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import chapter_digits, force_utf8_stdio, issue, padded


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    # Use escapes so this stays readable even in terminals with a legacy code page.
    parts = re.findall(r".*?(?:[\u3002\uff01\uff1f\uff1b!?;]+|$)", text, flags=re.S)
    return [part.strip() for part in parts if part.strip()]


def score_sentence(sentence: str, terms: list[str]) -> int:
    return sum(1 for term in terms if term and term in sentence)


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--chapter-id", type=int, required=True)
    parser.add_argument("--query", action="append", default=[], help="Keyword or phrase to search for. May be repeated.")
    parser.add_argument("--max-results", type=int, default=8)
    args = parser.parse_args()

    project_root = Path(args.project_root)
    pad = padded(args.chapter_id, chapter_digits(project_root))
    draft_path = project_root / "chapters" / f"{pad}.md"
    errors: list[dict[str, str]] = []

    try:
        draft = draft_path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        draft = ""
        errors.append(issue("draft_missing", "Draft/chapter file is missing.", path=str(draft_path)))

    terms = [item.strip() for item in args.query if item.strip()]
    sentences = split_sentences(draft)
    candidates = []
    for index, sentence in enumerate(sentences):
        if terms:
            score = score_sentence(sentence, terms)
            if score <= 0:
                continue
        else:
            score = 0
        candidates.append(
            {
                "index": index,
                "score": score,
                "evidence": sentence,
                "chars": len(sentence),
            }
        )

    candidates.sort(key=lambda item: (-item["score"], item["index"]))
    if args.max_results > 0:
        candidates = candidates[: args.max_results]

    result = {
        "schema_version": 1,
        "passed": not errors,
        "errors": errors,
        "query": terms,
        "results": candidates,
        "stats": {"sentences": len(sentences), "returned": len(candidates)},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
