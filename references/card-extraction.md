# Card Extraction

Cards are immutable chapter events. Extract a card from the final draft after
EditorReview passes.

## Inputs

Read:

1. final draft,
2. `contracts/<id>.json`,
3. `packets/<id>.json`,
4. `plans/chapters/<id>.json`,
5. `reviews/<id>.md`.

Do not read old chapters. Do not use projections to invent changes. Projections
may explain current state, but the card records what this chapter actually
changed and what the draft proves.

## Include In Card

Include only future-relevant information:

- major scene events with participants or location,
- entity state changes that future chapters need,
- knowledge changes,
- relationship phase changes,
- thread advances, pauses, resolutions, locks, and next review chapters,
- obligations resolved, superseded, continued, or created,
- locks asserted or still protected,
- reader-facing promises that future chapters must remember.

Do not include:

- mood without state effect,
- metaphors,
- routine movement with no future relevance,
- repeated background facts,
- speculation not established by the narrative,
- editor opinions.

## Evidence

Every event or change that can affect future writing must include an `evidence`
string copied verbatim from the draft. Keep evidence short enough to audit, but
long enough to prove the transition.

Good evidence proves an action, decision, revelation, transfer, promise, or
relationship turn. Weak evidence that only mentions a character name is not
enough.

If no evidence can support a claimed change, do not include the change. If the
contract required the change, halt because the draft did not actually satisfy
the contract.

## Contract Alignment

- A thread event must match `allowed_thread_moves`.
- A relationship change must match `relationship_bounds`.
- A removed lock must appear in `contract.allowed_reveals`.
- Every `resolve_now` obligation must be resolved, superseded, or transformed
  into a valid outgoing obligation.
- Every new outgoing obligation must have a stable id, text, mode, and
  source_chapter.

## Ambiguity

When the draft implies but does not prove a state change:

- Prefer no card change.
- Add an outgoing obligation only if the chapter clearly creates a future debt.
- Log the ambiguity in the run log `degraded_assumptions`.

Do not promote interpretation into truth.

## Output

Write `cards/<padded_id>.json` matching `chapter-card-format.md`.

Cards should be short. A useful card is closer to an event receipt than a
summary essay.
