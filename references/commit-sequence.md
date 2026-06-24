# Commit Sequence

The main agent writes all Novello files itself. Do not delegate commit to Writer or
EditorReview.

## Order

Write or verify files in this order:

```text
1. contracts/<padded_id>.json
2. packets/<padded_id>.json
3. chapters/<padded_id>.md
4. reviews/<padded_id>.md
5. cards/<padded_id>.json
6. logs/runs.jsonl                 (append pending/commit record if needed)
7. projections/*.json              (run rebuild_projections.py --write)
8. logs/runs.jsonl                 (append completed or failed final record)
```

If a run writes chapter prose but fails before a valid card, treat the run as
`partial_commit`. Do not delete written artifacts.

## Status Model

### halted

Use when the run stops before writing chapter prose.

```json
{"status":"halted","chapter_id":22,"stage":"packet","reason":"","repair_hint":"","run_id":""}
```

### partial_commit

Use when chapter prose, review, card, or a pending log was written but the run
cannot complete.

```json
{
  "status": "partial_commit",
  "chapter_id": 22,
  "stage": "validate_card|projection_rebuild|log",
  "files_written": [],
  "validation_errors": [],
  "recovery_hint": "Inspect written artifacts, preserve prose unless the user asks to rewrite, then resume from the first invalid step.",
  "run_id": ""
}
```

### completed

Use only after chapter, review, card, final log append, and projection rebuild
all succeed.

## Recovery Boundaries

- Do not automatically recover a partial commit during a normal run.
- Do not delete already-written files.
- Do not rewrite chapter prose unless the user explicitly asks.
- If the card is invalid, fix card only when the draft evidence supports the
  fix. Otherwise revise the draft under user instruction.
- If projection rebuild fails after a valid card, keep the card and log
  `partial_commit`; recovery should rebuild projections after the issue is
  fixed.

## Final Verification

Before reporting success:

1. `chapters/<id>.md`, `reviews/<id>.md`, and `cards/<id>.json` exist and are
   non-empty.
2. `scripts/validate_card.py` passes.
3. `scripts/rebuild_projections.py --write` passes.
4. The last non-empty line in `logs/runs.jsonl` parses as JSON with
   `status: "completed"`, matching `chapter_id`, and matching `run_id`.
5. Projection files exist and parse as JSON.

## User Report

On success:

```text
Chapter <id> committed.
Files: chapters/<id>.md, reviews/<id>.md, cards/<id>.json
Writer revisions: <count>
Card events: <count>
Projection rebuild: passed
```

On halt or partial commit, report the status, stage, reason, and recovery hint.
