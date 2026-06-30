# Contract Generation

Chapter contracts are written before drafting. They are not outlines. They are
permission boundaries for state, thread, relationship, knowledge, reveal, and
obligation changes.

## Inputs

Read only:

1. `plans/chapters/<id>.json`
2. `story_bible.json`
3. `style_guide.md` only for chapter-specific style constraints if the plan asks
4. `projections/entities.current.json`
5. `projections/relationships.current.json`
6. `projections/threads.current.json`
7. `projections/obligations.open.json`
8. `projections/reader_memory.current.json` only for recent reader-facing promises

Do not read full old chapters while building the contract. If exact old wording
is required, put that need into `required_evidence_in_draft` or a packet note;
do not broaden context.

## Contract Intent

A contract answers:

- what must be satisfied,
- what may move,
- what must remain locked,
- what relationship phases may change,
- what draft evidence must exist,
- where the ending must land.

It should be narrow enough to prevent drift and broad enough to let the scene
breathe. Do not enumerate normal prose texture.

## Build Rules

1. Start from the chapter plan's concrete goals, required reveals, forbidden
   reveals, planned threads, planned relationships, and ending hook.
2. Add every open obligation with `mode: resolve_now` or
   `avoid_contradiction`. Also add any obligation, regardless of mode, whose
   `due_chapter` is at or before this chapter, because the card must settle it
   here or the thread is dropped.
3. Add high-priority thread states whose `next_review_chapter <= chapter_id`.
4. Copy locks from active threads into `knowledge_locks` unless this chapter is
   explicitly allowed to reveal them.
5. For every thread that may change, add one `allowed_thread_moves` item. Keep
   `allowed_to` short: usually one or two next states.
6. For every relationship that may change, add one relationship bound. Default
   to beat-only movement: `allowed_moves: []`,
   `allowed_relationship_beats: [...]`, and `forbid_phase_transition: true`.
   Use a real phase transition only when the chapter plan explicitly requires
   it; then list the next plausible phase in `allowed_moves` and do not set
   `forbid_phase_transition: true`. Never allow an entire romance arc.
7. Add `allowed_reveals` only for reveals explicitly required by the plan or
   obligation. Everything else remains locked.
8. Add `required_evidence_in_draft` for concrete beats that must be visible in
   prose, such as a choice, discovery, refusal, promise, transfer, or reveal.
9. Set `packet_budget_chars` to the smallest budget that can safely cover the
   chapter. Default to 5000.
10. Set `risk_level` and `requires_adversarial_review: true` when this chapter
    carries a major reveal, a relationship phase transition, or settles a
    high-priority `reader_promise`. Leave them off for routine chapters so the
    main flow stays light.

## Halt Conditions

Halt before writing a contract when:

- A required reveal is also locked and the plan does not explicitly unlock it.
- The plan requires a thread or relationship move with no known current state.
- The plan requires resolving an obligation but does not say how, and choosing
  would change story direction.
- The contract would need to allow a leap larger than one plausible phase.
- A planned relationship moment is only a beat, but the contract can express it
  only by pretending a phase transition happened. Use a beat-only relationship
  bound instead.
- The target chapter already has a non-empty contract and the user did not ask
  for regeneration or revision.

## Output

Write `contracts/<padded_id>.json` matching `contract-format.md`.

Use stable ids. Prefer existing thread, relationship, entity, and obligation ids
from projections. When creating a new obligation id, use:

```text
obl:c<padded_id>_<short_slug>
```

Keep contract prose concise. The contract is for control, not style.
