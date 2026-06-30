---
name: novello
description: "Contract-first long-form novel writing for Novello file projects. Use when Codex should brainstorm or bootstrap a new novel project, turn a loose premise into story bible/style/plan files, or write/continue/review/maintain a long novel with immutable chapter cards, generated projections, bounded chapter packets, narrative thread scheduling, and anti-continuity-drift checks."
---

# Novello

Novello is a contract-first, event-sourced writing workflow for long novels.

Core rule:

```text
chapters/*.md = literary source
cards/*.json = only structured truth source
projections/*.json = generated, disposable memory
contracts/*.json and packets/*.json = per-chapter working inputs
reviews/*.md = editorial gate
logs/runs.jsonl = audit trail
```

The skill should remain a skill, not a platform. Prefer compact protocols,
deterministic validation scripts, and bounded agent passes. Add new machinery
only when it protects chapter quality, continuity, or recovery.

## Modes

Novello has two modes:

1. **ProjectBootstrap** - use when the user wants to start a new novel, develop
   a premise, explore story direction, or create project files.
2. **ChapterRun** - use when the user gives a target `chapter_id` or asks to
   continue/write/review a chapter in an existing Novello project.

For ProjectBootstrap, read `references/project-bootstrap.md`. Do not run the
chapter pipeline until the user has approved a project brief and project files
exist.

For ChapterRun, input is one target `chapter_id`.

Do not ask the user for confirmation during an active run unless a reference
file says to halt for human direction. Halt rather than improvise when contract
boundaries, Writer isolation, card evidence, or commit safety cannot be
maintained.

## Execution Boundaries

- Writer reads only the packet, contract, chapter plan, target language, and
  target length.
- Only the main Codex agent writes project files.
- Contracts, packets, reviews, and cards may be produced by bounded main-agent
  passes or sub-agents, but the main agent must validate and commit them.
- Treat scripts as deterministic guardrails. Read or patch script source only
  when debugging, extending validators, or the user asks.
- Do not use old prose as Writer context unless the contract explicitly
  requires exact wording and the packet includes only the needed excerpt.
- Do not manually treat projections as truth. Fix cards, then rebuild
  projections.

## ChapterRun Workflow

Track these stages during every run:

1. **Preflight**
   - Confirm `novello.json`, `plans/chapters/<id>.json`, and required
     directories exist.
   - If the chapter plan is missing, run
     `scripts/generate_chapter_plan.py --project-root <project_root> --chapter-id <id> --write`
     to create a conservative draft plan from open obligations, due threads,
     and the global arc. Review and refine the plan before building the
     contract; halt if the generated draft cannot express the next chapter
     without guessing story direction.
   - Halt if `chapters/<id>.md`, `cards/<id>.json`, or `logs/runs.jsonl`
     indicates the chapter already completed and the user did not request
     revision or recovery.

2. **RebuildProjections**
   - Run `scripts/rebuild_projections.py --project-root <project_root> --write`.
   - Treat generated `projections/*.json` as hot memory, not truth.
   - If rebuild fails before any new chapter artifact is written, halt.

3. **BuildContract**
   - Produce `contracts/<id>.json` using `references/contract-generation.md`
     and `references/contract-format.md`.
   - The contract defines what this chapter may change before drafting.
   - Halt if the contract allows a forbidden reveal, contradicts a locked
     thread, or cannot express required chapter movement without guessing.

4. **BuildPacket**
   - Produce `packets/<id>.json` using `references/packet-generation.md` and
     `references/packet-format.md`.
   - The packet is the only prose-generation context passed to Writer.
   - Run `scripts/validate_packet.py --project-root <project_root> --chapter-id <id>`.
     When validating a packet after the target chapter may already have a card
     on disk, add `--rebuild-as-of` so validation ignores cards from the target
     chapter and later.
   - Halt if packet validation fails.

5. **WriteDraft**
   - Run Writer using `references/writer-protocol.md`.
   - Writer returns draft prose plus self-check and contract-check.
   - If high/blocker issues remain, revise within the protocol budget.
   - Halt if Writer cannot satisfy the contract after the allowed revisions.

6. **EditorReview**
   - Produce `reviews/<id>.md` using `references/editor-review.md`.
   - The review is a literary and contract-experience gate, not a second canon
     store.
   - When the contract sets `requires_adversarial_review: true` (or the user
     asks for strict review), run one adversarial pass using
     `references/adversarial-review-protocol.md` before finalizing the verdict.
     Do not run it on every chapter; reserve it for high-risk chapters.
   - If the review finds blocker issues, revise once if the Writer budget
     allows; otherwise halt.

7. **RetconScan**
   - Before card extraction, run the compact RetconScan from
     `references/editor-review.md`.
   - The scan is not a second literary review. It checks whether the draft
     introduced durable facts, knowledge leaks, relationship jumps, obligation
     changes, or reader promises outside the contract/packet.
   - Fold the result into `reviews/<id>.md`. Halt or revise when it finds an
     uncontracted continuity change.
   - Run `scripts/validate_review.py --project-root <project_root> --chapter-id <id>`.
     Halt or repair the review if validation fails.

8. **ExtractCard**
   - Produce `cards/<id>.json` from the final draft using
     `references/card-extraction.md` and `references/chapter-card-format.md`.
   - Every future-relevant state change must have evidence copied from the
     draft.
   - When exact draft evidence is hard to locate, use
     `scripts/suggest_evidence.py --project-root <project_root> --chapter-id <id> --query <term>`.

9. **ValidateCard**
   - Run `scripts/validate_card.py --project-root <project_root> --chapter-id <id>`.
   - Halt if the card claims an uncontracted transition, removes a lock without
     permission, misses required evidence, leaves a resolve-now obligation
     unsettled, drops an obligation past its `due_chapter`, or fails schema
     validation.

10. **CommitAndRebuild**
   - Commit in the order defined by `references/commit-sequence.md`.
   - Rebuild projections after committing and validating the card.
   - Append the completed run log using `scripts/append_run_log.py` and
     `references/run-log-schema.md` only after packet validation, card
     validation, and projection rebuild reports all passed.
   - Validate that the final log line and projection files both succeeded.

## Failure Boundaries

Use `references/transition-rules.md` for severity and repair decisions. Halt
rather than improvise when:

- The target chapter already exists and the user did not request recovery or
  revision.
- A contract allows a reveal forbidden by projection locks.
- A high-priority overdue thread is absent from the packet.
- A packet omits a `resolve_now` or `avoid_contradiction` obligation.
- A packet omits an obligation whose `due_chapter` is at or before this chapter.
- A card lets an obligation pass its `due_chapter` without settling it.
- Writer cannot satisfy the contract within the revision budget.
- EditorReview finds a blocker and no allowed revision remains.
- RetconScan finds an uncontracted durable fact, knowledge leak, relationship
  jump, obligation change, or new reader promise that cannot be removed or
  explicitly handled within the contract.
- A card state change lacks draft evidence.
- A card claims a transition not allowed by the contract.
- ValidateCard fails.
- Projection rebuild fails after the card is committed.

Report halted runs in the compact format from `references/commit-sequence.md`.

## Reference Routing

- `references/project-bootstrap.md` - interactive novel idea development and project materialization
- `references/project-layout.md` - project files and generated/disposable boundaries
- `references/contract-generation.md` - how to create chapter contracts
- `references/contract-format.md` - chapter contract schema and intent
- `references/packet-generation.md` - how to assemble bounded Writer packets
- `references/packet-format.md` - packet schema
- `references/writer-protocol.md` - isolated Writer role and output rules
- `references/editor-review.md` - literary review gate
- `references/adversarial-review-protocol.md` - optional high-risk adversarial review
- `references/card-extraction.md` - extracting immutable chapter cards
- `references/chapter-card-format.md` - card schema
- `references/transition-rules.md` - continuity, reveal, thread, and relationship rules
- `references/commit-sequence.md` - commit order, recovery, and status model
- `references/run-log-schema.md` - completed and failed run log shapes

## Scripts

- `scripts/rebuild_projections.py` - replay cards into generated projections
- `scripts/generate_chapter_plan.py` - draft a missing next chapter plan from projections and arc data
- `scripts/validate_packet.py` - validate packet coverage against projections and contract
- `scripts/validate_review.py` - validate EditorReview and RetconScan structure
- `scripts/validate_card.py` - validate card transitions and draft evidence
- `scripts/suggest_evidence.py` - suggest exact draft snippets for card evidence
- `scripts/append_run_log.py` - append completed run logs from passed validator reports

Scripts do not judge literary quality. Codex owns contract judgment, prose,
review, card extraction, and final reporting.
