# Run Log Schema

Novello runs append JSON lines to `logs/runs.jsonl`. Logs are audit records, not
truth. Cards remain the only structured truth source.

## Completed Run

```json
{
  "schema_version": 1,
  "status": "completed",
  "chapter_id": 22,
  "run_id": "20260624T120000_ch22",
  "contract": {
    "path": "contracts/000022.json",
    "generated": true,
    "halted_reasons": []
  },
  "packet_validation": {
    "passed": true,
    "errors": [],
    "warnings": [],
    "stats": {}
  },
  "writer": {
    "revision_count": 0,
    "new_facts": []
  },
  "editor_review": {
    "path": "reviews/000022.md",
    "verdict": "pass",
    "issues": []
  },
  "card_validation": {
    "passed": true,
    "errors": [],
    "warnings": [],
    "stats": {}
  },
  "projection_rebuild": {
    "passed": true,
    "errors": [],
    "stats": {}
  },
  "files_committed": [],
  "degraded_assumptions": []
}
```

Required fields: `schema_version`, `status`, `chapter_id`, `run_id`,
`contract`, `packet_validation`, `writer`, `editor_review`, `card_validation`,
`projection_rebuild`, `files_committed`, `degraded_assumptions`.

## Halted Run

```json
{
  "schema_version": 1,
  "status": "halted",
  "chapter_id": 22,
  "run_id": "20260624T120000_ch22",
  "stage": "contract",
  "reason": "",
  "repair_hint": "",
  "files_written": []
}
```

Use only before chapter prose is written.

## Partial Commit Run

```json
{
  "schema_version": 1,
  "status": "partial_commit",
  "chapter_id": 22,
  "run_id": "20260624T120000_ch22",
  "stage": "validate_card",
  "reason": "",
  "files_written": [],
  "validation_errors": [],
  "recovery_hint": ""
}
```

Use after any chapter prose, review, card, or pending run log artifact exists
and the run cannot complete.

## Logging Rules

- Do not store full draft prose in logs.
- Do not store full packet text unless needed for a failure reason.
- Store paths, validation reports, counts, warnings, compactness stats, and
  degraded assumptions.
- The final completed line must be last. If a pending or partial line was
  written earlier, append a new completed line after recovery succeeds.
