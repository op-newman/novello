# Novello

Novello is a Codex skill for contract-first long-form novel writing.

It keeps long novels manageable by separating literary prose from structured
memory:

```text
chapters/*.md = literary source
cards/*.json = only structured truth source
projections/*.json = generated memory
contracts/*.json = allowed chapter movement
packets/*.json = bounded Writer context
reviews/*.md = editorial gate
logs/runs.jsonl = audit trail
```

The workflow is designed for continuity-heavy fiction where each chapter must
advance story threads without leaking locked reveals, skipping relationship
phases, or letting state drift across a long manuscript.

## What It Does

Novello supports two connected workflows.

Project bootstrap turns a loose idea into project front matter:

1. Explore the user's creative direction through conversation.
2. Converge on a project brief.
3. Materialize `story_bible.json`, `style_guide.md`, global/arc plans, and the
   first chapter plan after user confirmation.

Chapter run guides Codex through a complete chapter:

1. Rebuild generated projections from immutable chapter cards.
2. Create a chapter contract that defines what may change.
3. Build a bounded packet for the Writer.
4. Draft the chapter from only the packet, contract, plan, and target length.
5. Review the draft for literary quality and contract experience.
6. Extract an evidence-backed chapter card.
7. Validate the card against the contract and draft.
8. Commit chapter artifacts and rebuild projections.

## Project Layout

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
  logs/runs.jsonl
```

See [references/project-layout.md](references/project-layout.md) for the full
layout and [references/project-bootstrap.md](references/project-bootstrap.md)
for the interactive bootstrap protocol.

## Install As A Codex Skill

Place this repository folder under your Codex skills directory, for example:

```text
~/.codex/skills/novello
```

Then ask Codex to use Novello with a target chapter id.

## Validation Scripts

The bundled scripts provide deterministic guardrails:

```bash
python scripts/rebuild_projections.py --project-root <project_root> --write
python scripts/generate_chapter_plan.py --project-root <project_root> --chapter-id <id> --write
python scripts/validate_packet.py --project-root <project_root> --chapter-id <id>
python scripts/validate_review.py --project-root <project_root> --chapter-id <id>
python scripts/validate_card.py --project-root <project_root> --chapter-id <id>
python scripts/suggest_evidence.py --project-root <project_root> --chapter-id <id> --query <term>
python scripts/append_run_log.py --project-root <project_root> --chapter-id <id> \
  --packet-report <packet_report.json> --card-report <card_report.json> \
  --projection-report <projection_report.json>
```

Scripts validate structure and continuity boundaries. They do not judge prose
quality; the skill's EditorReview pass handles literary review.

## Tests

Run the script tests from the repository root:

```bash
python tests/test_scripts.py
```

## License

MIT
