# Chapter Contract Format

The contract is written before drafting. It defines what the chapter may change.

Required top-level fields:

```json
{
  "schema_version": 1,
  "chapter_id": 22,
  "title": "",
  "source_plan": "plans/chapters/000022.json",
  "must_satisfy": [],
  "allowed_thread_moves": [],
  "allowed_reveals": [],
  "relationship_bounds": {},
  "knowledge_locks": [],
  "required_evidence_in_draft": [],
  "ending_target": "",
  "packet_budget_chars": 5000
}
```

Thread move:

```json
{
  "thread_id": "thread:lin_father_old_case",
  "from": "old_archive_coordination_role",
  "allowed_to": ["gu_family_pressure"],
  "forbidden_to": ["handler_identity_revealed", "accident_truth_revealed"]
}
```

Relationship bound:

```json
{
  "char:lin_wanxing__char:gu_yanzhou": {
    "current": "limited_collaboration_with_returned_choice",
    "allowed_moves": ["choice_respected_under_pressure"],
    "forbidden_moves": ["confession", "formal_love", "coercive_control_romanticized"]
  }
}
```

Beat-only relationship bound:

```json
{
  "char:lin_wanxing__char:gu_yanzhou": {
    "current": "limited_collaboration_with_returned_choice",
    "allowed_moves": [],
    "allowed_relationship_beats": ["toward_choice_respected_under_pressure"],
    "forbidden_moves": ["confession", "formal_love", "coercive_control_romanticized"],
    "forbid_phase_transition": true
  }
}
```

Use contracts to prevent the card from inventing a larger transition than the
chapter was allowed to perform.

Field intent:

- `must_satisfy`: hard chapter requirements that affect continuity, obligation
  settlement, reveal timing, or the promised ending. Do not use this field for
  broad literary goals such as "make the scene tense" or "show longing"; put
  those in packet `non_canon_dramatic_guidance`.
- `allowed_thread_moves`: thread transitions this chapter may make.
- `allowed_reveals`: locked facts this chapter may reveal. Omit or keep empty
  when no reveal is permitted.
- `relationship_bounds`: current and allowed next phases or beat directions for
  relationship pairs.
- `knowledge_locks`: facts that must remain unknown or unconfirmed.
- `required_evidence_in_draft`: exact required beats that must appear in this
  target chapter's prose. Do not put prior-chapter planted evidence here; use
  `obligations_in.evidence_ref` to prove fulfillment of earlier obligations.
- `ending_target`: the required final turn, image, decision, or discovery.
- `packet_budget_chars`: maximum packet size.

Optional control fields:

- `risk_level`: one of `low`, `medium`, `high`. Mark a chapter `high` when it
  carries a major reveal, a relationship phase transition, or another move that
  is costly to get wrong.
- `requires_adversarial_review`: boolean. Set `true` to request an extra
  adversarial review pass before card extraction. Omit or set `false` for
  ordinary chapters so the main pipeline stays light.

Validation rules:

- Every thread or relationship state change claimed by a card must be listed in
  this chapter's contract.
- `allowed_to` and `forbidden_to` must not contain the same thread state.
- `allowed_moves` and `forbidden_moves` must not contain the same relationship
  state.
- A relationship bound may be beat-only: set `allowed_moves: []`, list one or
  more `allowed_relationship_beats`, and set `forbid_phase_transition: true`.
  This permits gradual movement without allowing a real `from`/`to` phase
  transition.
- When `allowed_relationship_beats` is non-empty, a card `relationship_beat`
  for that pair must use one listed `direction`. If the field is omitted, beat
  validation only enforces `forbidden_moves`.
- `forbid_phase_transition: true` must not be combined with non-empty
  `allowed_moves`.
- No allowed beat direction may contain a forbidden move name.
- Every `must_satisfy` item must appear in the packet. Literary goals that do
  not require cardable state should not be listed as `must_satisfy`.
- `ending_target` must be carried into the packet.
- Every `required_evidence_in_draft` string must appear in the final draft of
  this target chapter.
- A lock may be removed from a thread only when the removed lock appears in
  `allowed_reveals`.
