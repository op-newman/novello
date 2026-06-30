# Project Layout

Novello uses immutable chapter cards plus generated projections.

```text
project/
  novello.json
  story_bible.json
  style_guide.md
  plans/chapters/000001.json
  chapters/000001.md
  contracts/000001.json
  packets/000001.json
  reviews/000001.md
  cards/000001.json
  projections/
    entities.current.json
    relationships.current.json
    threads.current.json
    obligations.open.json
    reader_memory.current.json
  logs/runs.jsonl
```

Truth boundaries:

- `chapters/*.md`: full prose archive.
- `cards/*.json`: only structured truth source.
- `projections/*.json`: generated from cards; safe to delete and rebuild.
- `contracts/*.json`: allowed moves for a target chapter.
- `packets/*.json`: bounded writer input, generated from projection + contract + plan.
- `reviews/*.md`: editorial critique and revision notes.

Do not manually treat projection files as truth. If projection output is wrong,
fix the relevant card and rebuild.

Chapter ids use six digits by default unless `novello.json.chapter_digits`
overrides it.

An empty new project is valid before chapter 1. In that state, `cards/` is
empty and `rebuild_projections.py --write` should create empty projections.
The first chapter then establishes the initial structured truth through its
card.

If `plans/chapters/<id>.json` is missing during a chapter run, generate a
conservative draft with:

```bash
python scripts/generate_chapter_plan.py --project-root <project_root> --chapter-id <id> --write
```

The generated plan is a safety draft, not final creative judgment. Refine it
before writing the contract when the next chapter needs a sharper premise.

Optional compactness settings in `novello.json`:

```json
{
  "card_soft_budget_chars": 5500,
  "card_soft_projection_items": 22,
  "card_soft_evidence_items": 24
}
```

These are warning thresholds for `validate_card.py`. They help track long-run
memory weight without blocking chapters that genuinely need denser state.
