# Chapter Card Format

Cards are immutable structured events. They are the only structured truth source.

Required fields:

```json
{
  "schema_version": 1,
  "chapter_id": 21,
  "title": "",
  "summary": "",
  "evidence": [],
  "events": [],
  "entity_changes": [],
  "knowledge_changes": [],
  "relationship_changes": [],
  "thread_events": [],
  "obligations_in": [],
  "obligations_out": [],
  "locks_asserted": []
}
```

Required fields: `schema_version`, `chapter_id`, `title`, `summary`,
`events`, `entity_changes`, `knowledge_changes`, `relationship_changes`,
`thread_events`, `obligations_in`, `obligations_out`, and `locks_asserted`.
Cards must include top-level `evidence`.

Evidence pool:

```json
{
  "evidence": [
    {
      "id": "ev1",
      "quote": "Lin placed the archive key in Gu's palm."
    }
  ]
}
```

Every event or change that affects future writing should use `evidence_ref`:

```json
{
  "text": "Lin returned the archive key to Gu.",
  "evidence_ref": "ev1"
}
```

`events[]` items with `participants` or `location` mutate generated projections
and therefore must include `evidence_ref`.

Thread event:

```json
{
  "thread_id": "thread:old_case",
  "action": "advance",
  "from": "archive_door_pending",
  "to": "archive_opened_truth_locked",
  "still_locked": ["handler_identity", "accident_responsibility", "accident_truth"],
  "next_review_chapter": 24,
  "evidence_ref": "ev1"
}
```

Relationship change:

```json
{
  "pair": ["char:lin", "char:gu"],
  "from": "strained_trust",
  "to": "limited_collaboration",
  "evidence_ref": "ev2"
}
```

Relationship beat (gradual progress without a phase transition):

```json
{
  "type": "relationship_beat",
  "pair": ["char:lin", "char:gu"],
  "current_phase": "strained_trust",
  "direction": "toward_limited_collaboration",
  "intensity": "small",
  "evidence_ref": "ev3"
}
```

Use a beat to record that the pair moved closer without crossing into a new
phase yet. A beat must not assert a `to` phase; its `current_phase` must match
the current projection phase. The pair must have a relationship bound in the
contract. If that bound includes `allowed_relationship_beats`, the beat
`direction` must match one listed value; otherwise the direction is free-form
but must not name a move the contract forbids for the pair. Beats accumulate in
the projection as evidence so a later contract can decide whether a real
`from`/`to` transition is earned. Do not quantify a beat with a numeric score;
record the concrete evidence instead.

Knowledge change:

```json
{
  "character_id": "char:lin",
  "fact": "accident_truth",
  "status": "suspected",
  "evidence_ref": "ev4"
}
```

`status` is `suspected` (the character senses something but has not confirmed
it) or `known` (the character holds the fact as confirmed). A fact listed in the
contract's `knowledge_locks` may only reach `known` when that fact also appears
in `allowed_reveals`; otherwise the lock is broken and `validate_card.py` fails.
A locked fact may still move to `suspected`, because suspicion keeps the fact
unconfirmed and within the lock.

Obligations use stable ids. Resolve by `id`; keep `text` for human readability:

```json
{
  "obligations_in": [{"id": "obl:c021_touch_old_case", "status": "resolved"}],
  "obligations_out": [
    {
      "id": "obl:c022_keep_truth_locked",
      "text": "Keep the accident truth locked until chapter 24.",
      "mode": "avoid_contradiction",
      "source_chapter": 22,
      "due_chapter": 24
    }
  ]
}
```

An outgoing obligation may carry an optional `type`. Use `type: "reader_promise"`
for a promise the reader will remember and expect paid off, such as a deadline,
a vow, or a planted foreshadow. A `reader_promise` requires two extra fields:

```json
{
  "id": "obl:c012_archive_key_return",
  "type": "reader_promise",
  "text": "Lin must return or explain the archive key.",
  "mode": "resolve_now",
  "source_chapter": 12,
  "due_chapter": 25,
  "priority": "high",
  "planted_evidence_ref": "ev5",
  "fulfillment_conditions": [
    "Lin returns the key",
    "OR Lin explains why she cannot",
    "OR the deadline is explicitly extended"
  ]
}
```

- `planted_evidence_ref`: the evidence id whose quote established the promise.
- `fulfillment_conditions`: at least one concrete way the promise can be settled.
- `due_chapter`, when present, must be later than `source_chapter`.

Any obligation that reaches its `due_chapter` must be settled by the card on or
before that chapter: resolved or superseded in `obligations_in`, or re-emitted
as a new outgoing obligation. An expired obligation that simply disappears is a
dropped thread and fails validation.

Cards should be short but not vague. Only future-relevant information belongs
in a card.

Do not store review commentary, style notes, or full chapter summaries in cards.
Cards are evidence-backed state events, not literary analysis.

## Proof Authority Boundary

`summary`, `text`, `action`, and similar human-readable fields have no proof
authority. They help readers and projections label events, but only
`evidence[]` quotes referenced by `evidence_ref` or `planted_evidence_ref`
prove a state change.

Evidence reuse is a discipline, not magic. If two card items rely on the same
draft fact, reuse one evidence id. Validators check that refs exist and quotes
appear in the draft; they do not infer whether two separate evidence ids prove
the same semantic fact.

Empty change lists are valid. A chapter may produce no entity, knowledge,
relationship, thread, or obligation changes. Do not turn atmosphere, tone,
subtext, or routine movement into card state merely to fill the schema.

`validate_card.py` reports soft compactness warnings and stats such as
`card_chars`, `projection_items`, and `evidence_count`. These warnings do not
fail validation; they flag cards that are starting to read like summaries
instead of receipts. Project-level `novello.json` may override
`card_soft_budget_chars`, `card_soft_projection_items`, and
`card_soft_evidence_items` when a genre genuinely needs denser cards.

`must_satisfy` items are hard chapter requirements, but they may still be
dramatized rather than repeated verbatim in the draft or card. Mechanical
validators require exact `required_evidence_in_draft` strings and settled
obligations, while EditorReview judges whether each required beat is visible to
a reader.
