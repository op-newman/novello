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

Packet `non_canon_dramatic_guidance`, review notes, RetconScan notes, style
anchors, and any interpretation of subtext are not evidence. They may explain
why a scene was written, but they must not be used to create card facts. If the
final draft does not explicitly prove a future-relevant change, leave it out of
the card.

## Include In Card

Include only future-relevant information:

- major scene events with participants or location,
- entity state changes that future chapters need,
- knowledge changes,
- relationship phase changes,
- relationship beats: gradual movement toward a phase that has not crossed yet,
- thread advances, pauses, resolutions, locks, and next review chapters,
- obligations resolved, superseded, continued, or created,
- a reader_promise obligation for any deadline, vow, or planted foreshadow the
  reader will remember and expect paid off,
- locks asserted or still protected,
- reader-facing promises that future chapters must remember.

Do not include:

- mood without state effect,
- metaphors,
- routine movement with no future relevance,
- repeated background facts,
- speculation not established by the narrative,
- editor opinions.
- packet or review interpretations that are not explicitly proven in the final
  draft.

## Evidence

New cards should use top-level `evidence[]` and per-item `evidence_ref`. Each
evidence item contains an `id` and a `quote` copied verbatim from the draft. Keep
quotes short enough to audit, but long enough to prove the transition.

Evidence reuse reduces inconsistency but does not replace judgment. If two card
items rely on the same draft fact, reuse one evidence id. Validators do not
infer semantic identity between separate evidence ids.

Good evidence proves an action, decision, revelation, transfer, promise, or
relationship turn. Weak evidence that only mentions a character name is not
enough.

If no evidence can support a claimed change, do not include the change. If the
contract required the change, halt because the draft did not actually satisfy
the contract.

Evidence proves only what the quoted draft text explicitly establishes. Do not
use a quote plus packet guidance or review interpretation to infer a stronger
truth than the words on the page support.

When searching for exact evidence, use the helper rather than paraphrasing from
memory:

```bash
python scripts/suggest_evidence.py --project-root <project_root> --chapter-id <id> --query <term>
```

Use only snippets that are exact substrings of the final draft.

## Extraction Protocol

Use Candidate -> Classify -> Prune -> Commit:

1. Candidate: list every possible future-relevant change the draft may have
   created.
2. Classify: decide which projection each candidate feeds: event/reader memory,
   entity state, knowledge state, relationship state/beat, thread state,
   obligation, or lock.
3. Prune: keep only candidates that pass all three questions:
   - Will future chapters write incorrectly if this is forgotten?
   - Does the contract allow this change?
   - Does one exact draft quote prove it without review or packet
     interpretation?
4. Commit: add one evidence quote to `evidence[]`, reuse its id across every
   projection item that the same quote proves, and write only the classified
   items that survived pruning.

Cross-type reuse is healthy: one evidence id may support an event, an entity
change, and a thread event because they feed different projections. Avoid
same-type duplication: do not write several overlapping events, entity changes,
or thread events that assert the same state.

An empty or near-empty card is valid and healthy. If a chapter is atmosphere,
transition, or daily texture without future-relevant state changes, do not
invent changes to fill the card. Prefer an honest empty card over fabricated
state.

## Contract Alignment

- A thread event must match `allowed_thread_moves`.
- A relationship change must match `relationship_bounds`.
- A removed lock must appear in `contract.allowed_reveals`.
- A `knowledge_change` may not set a `contract.knowledge_locks` fact to `known`
  unless that fact is in `contract.allowed_reveals`. A character may reach
  `suspected` while the fact stays locked, but confirmed knowledge of a locked
  fact is a leak and fails validation.
- Every `resolve_now` obligation must be resolved, superseded, or transformed
  into a valid outgoing obligation.
- Every new outgoing obligation must have a stable id, text, mode, and
  source_chapter.
- Every obligation whose `due_chapter` has arrived must be settled this chapter:
  resolved or superseded in `obligations_in`, or re-emitted as a new outgoing
  obligation. A due obligation may not silently disappear.

## Reader Promises

When the chapter plants something the reader will remember and expect paid off
(a deadline, a vow, a planted foreshadow), record it as an outgoing obligation
with `type: "reader_promise"`. It needs `planted_evidence_ref` pointing to the
draft quote that planted the promise and at least one `fulfillment_conditions`
entry. Set `due_chapter` to the
chapter by which the promise must land. Do not invent a promise the draft did
not actually make.

## Relationship Beats

When the draft moves a pair closer but does not cross into a new phase, record a
`relationship_beat` instead of forcing a `from`/`to` transition. A beat carries
`current_phase` (matching the projection), `direction`, `intensity`, and
`evidence_ref`. It must not assert a `to` phase, and its `direction` must not name a
move the contract forbids for the pair. If the contract lists
`allowed_relationship_beats`, the beat `direction` must be one of those values.
If the contract omits that field, the beat is allowed as long as the pair has a
relationship bound and the direction does not violate `forbidden_moves`. Do not
attach a numeric score; the concrete evidence is the record. Reserve a real
`from`/`to` change for the chapter where the contract allows the phase to
actually cross.

## Ambiguity

When the draft implies but does not prove a state change:

- Prefer no card change.
- Add an outgoing obligation only if the chapter clearly creates a future debt.
- Log the ambiguity in the run log `degraded_assumptions`.

Do not promote interpretation into truth.

## Output

Write `cards/<padded_id>.json` matching `chapter-card-format.md`.

Cards should be short. A useful card is closer to an event receipt than a
summary essay. Prefer one precise evidence-backed item over several overlapping
items that all prove the same thing.
