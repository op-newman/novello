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
