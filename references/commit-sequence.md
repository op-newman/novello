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
5. validate review                 (run validate_review.py)
6. cards/<padded_id>.json
7. validate card                   (run validate_card.py)
8. projections/*.json              (run rebuild_projections.py --write)
9. logs/runs.jsonl                 (append completed or partial final record)
```

If a run writes chapter prose but fails before a valid card, treat the run as
`partial_commit`. Do not delete written artifacts.

Commit in this document means writing Novello chapter artifacts to disk. It does
not mean `git commit`.

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

Use only after chapter, review, card, card validation, projection rebuild, and
final log append all succeed.

## Recovery Boundaries

- Do not automatically recover a partial commit during a normal run.
- Do not delete already-written files.
- Do not rewrite chapter prose unless the user explicitly asks.
- If the card is invalid, fix card only when the draft evidence supports the
  fix. Otherwise revise the draft under user instruction.
- If projection rebuild fails after a valid card, keep the card and append a
  `partial_commit` log record; recovery should rebuild projections after the
  issue is fixed.

## Final Verification

Before reporting success:

1. `chapters/<id>.md`, `reviews/<id>.md`, and `cards/<id>.json` exist and are
   non-empty.
2. `scripts/validate_review.py` passes.
3. `scripts/validate_card.py` passes.
4. `scripts/rebuild_projections.py --write` passes.
   Do not use ordinary packet validation as a post-commit check for the same
   chapter; if auditing a completed chapter's packet, use `validate_packet.py
   --rebuild-as-of`.
5. Append the completed run log with `scripts/append_run_log.py`, passing saved
   packet, card, and projection reports whose `passed` value is `true`.
6. The last non-empty line in `logs/runs.jsonl` parses as JSON with
   `status: "completed"`, matching `chapter_id`, and matching `run_id`.
7. Projection files exist and parse as JSON.

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
