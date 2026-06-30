from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


class DuplicateKeyError(ValueError):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Duplicate JSON key: {key}")


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def force_utf8_stdio() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def read_json(path: Path, default: Any | None = None) -> Any:
    try:
        data = path.read_bytes()
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            if data.startswith((b"\xff\xfe", b"\xfe\xff")):
                text = data.decode("utf-16")
            else:
                raise
        return json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except FileNotFoundError:
        if default is not None:
            return default
        raise


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def padded(chapter_id: int, digits: int = 6) -> str:
    return str(chapter_id).zfill(digits)


def chapter_digits(project_root: Path) -> int:
    config = read_json(project_root / "novello.json", default={})
    value = config.get("chapter_digits", 6) if isinstance(config, dict) else 6
    return value if isinstance(value, int) and value > 0 else 6


def load_cards(project_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    cards_dir = project_root / "cards"
    cards: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    seen: dict[int, Path] = {}
    if not cards_dir.exists():
        return cards, errors
    for path in sorted(cards_dir.glob("*.json")):
        try:
            card = read_json(path)
        except DuplicateKeyError as exc:
            errors.append(issue("card_json_duplicate_key", f"Card JSON has duplicate key: {exc.key}", path=str(path)))
            continue
        except json.JSONDecodeError as exc:
            errors.append(issue("card_json_invalid", f"Card JSON is invalid: {exc}", path=str(path)))
            continue
        if not isinstance(card, dict):
            errors.append(issue("card_not_object", "Card root must be an object.", path=str(path)))
            continue

        chapter_id = card.get("chapter_id")
        filename_id: int | None = None
        if path.stem.isdigit():
            filename_id = int(path.stem)
        else:
            errors.append(issue("card_filename_not_numeric", "Card filename must be a numeric chapter id.", path=str(path)))

        if not isinstance(chapter_id, int) or chapter_id <= 0:
            errors.append(issue("card_chapter_id_invalid", "Card chapter_id must be a positive integer.", path=str(path)))
        else:
            if filename_id is not None and filename_id != chapter_id:
                errors.append(
                    issue(
                        "card_filename_chapter_mismatch",
                        f"Filename chapter {filename_id} does not match card chapter_id {chapter_id}.",
                        path=str(path),
                    )
                )
            if chapter_id in seen:
                errors.append(
                    issue(
                        "duplicate_card_chapter_id",
                        f"Duplicate chapter_id {chapter_id}; first seen at {seen[chapter_id]}.",
                        path=str(path),
                    )
                )
            else:
                seen[chapter_id] = path

        cards.append(card)

    if seen:
        max_chapter = max(seen)
        missing = [str(chapter_id) for chapter_id in range(1, max_chapter + 1) if chapter_id not in seen]
        if missing:
            sample = ", ".join(missing[:20])
            suffix = "..." if len(missing) > 20 else ""
            errors.append(issue("card_chapter_gap", f"Missing card chapter_id(s): {sample}{suffix}", path=str(cards_dir)))

    def sort_key(item: dict[str, Any]) -> int:
        chapter_id = item.get("chapter_id")
        return chapter_id if isinstance(chapter_id, int) else 0

    return sorted(cards, key=sort_key), errors


def iter_cards(project_root: Path) -> list[dict[str, Any]]:
    cards, _errors = load_cards(project_root)
    return cards


def issue(code: str, message: str, *, path: str | None = None) -> dict[str, str]:
    item = {"code": code, "message": message}
    if path:
        item["path"] = path
    return item
