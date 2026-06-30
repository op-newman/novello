# Transition Rules

Validators check cards and packets against these deterministic rules.

## Thread Rules

- A thread cannot move to a `forbidden_to` state in the chapter contract.
- A thread cannot remove a lock unless the contract explicitly allows the reveal.
- A high-priority thread with `next_review_chapter <= target chapter` must enter
  the packet, either as an active thread or as a must-not-do lock.
- `next_review_chapter` should move forward when a long arc is touched.

## Knowledge Rules

- A character can move from `unknown` to `suspected` or `known`.
- A move to `known` needs draft evidence.
- A character cannot know a locked reveal unless the contract allows it.
  `validate_card.py` enforces this: a `knowledge_changes` entry with
  `status: "known"` whose `fact` is in `contract.knowledge_locks` but not in
  `contract.allowed_reveals` fails as `knowledge_lock_violated`. `suspected`
  keeps the fact unconfirmed and stays within the lock.

## Relationship Rules

- Relationship changes must be listed in the contract's `allowed_moves`.
- Forbidden moves such as confession, formal love, or coercive romanticized
  control must halt unless explicitly allowed by a later contract.
- A `relationship_beat` records gradual progress without a phase transition. It
  must not assert a `to` phase, its `current_phase` must match the projection
  phase, and it needs `evidence_ref`. The pair must have a relationship bound in
  the contract. Beats accumulate in the projection so a later contract can
  decide whether a real `from`/`to` transition is earned. Do not attach a
  numeric progress score; record the concrete evidence instead.
- Contract generation should default to beat-only relationship bounds:
  `allowed_moves: []`, `allowed_relationship_beats: [...]`, and
  `forbid_phase_transition: true`. Then `validate_card.py` allows only listed
  beat directions and rejects real phase transitions. Real phase changes must be
  explicitly listed in `allowed_moves`.
- If `allowed_relationship_beats` is omitted, a beat's `direction` may still be
  free-form, but it may not name a phase the contract forbids. If a
  `forbidden_moves` phase appears as a substring of the beat's `direction` (for
  example `direction: "toward_formal_love"` when `formal_love` is forbidden),
  `validate_card.py` rejects it.

## Obligation Rules

- `resolve_now` obligations must be addressed in the packet and card.
- `avoid_contradiction` obligations must remain true after the card.
- New obligations should include `mode`, `text`, `source_chapter`, and optional
  `due_chapter`.
- Any obligation whose `due_chapter` is at or before the target chapter must be
  settled by the card: resolved or superseded in `obligations_in`, or re-emitted
  as a new outgoing obligation. A due obligation that simply vanishes is a
  dropped thread and fails `validate_card.py`.
- A `reader_promise` obligation must carry `planted_evidence_ref` and at least
  one `fulfillment_conditions` entry so the promise can be checked when it
  comes due.

## Evidence Rules

- New cards should store quotes in top-level `evidence[]` and reference them
  with `evidence_ref`.
- `validate_card.py` checks that every evidence quote appears verbatim in the
  chapter draft and every ref points to an existing evidence id.
- Evidence can be short. It should prove the transition, not quote large prose.
