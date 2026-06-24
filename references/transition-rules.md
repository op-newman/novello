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

## Relationship Rules

- Relationship changes must be listed in the contract's `allowed_moves`.
- Forbidden moves such as confession, formal love, or coercive romanticized
  control must halt unless explicitly allowed by a later contract.

## Obligation Rules

- `resolve_now` obligations must be addressed in the packet and card.
- `avoid_contradiction` obligations must remain true after the card.
- New obligations should include `mode`, `text`, `source_chapter`, and optional
  `due_chapter`.

## Evidence Rules

- Every card event/change that affects projections needs an `evidence` string.
- `validate_card.py` checks that evidence appears verbatim in the chapter draft.
- Evidence can be short. It should prove the transition, not quote large prose.
