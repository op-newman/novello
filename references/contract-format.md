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

Use contracts to prevent the card from inventing a larger transition than the
chapter was allowed to perform.

Field intent:

- `must_satisfy`: concrete beats, obligations, and plan goals that must appear
  in the packet and be settled by draft/card.
- `allowed_thread_moves`: thread transitions this chapter may make.
- `allowed_reveals`: locked facts this chapter may reveal. Omit or keep empty
  when no reveal is permitted.
- `relationship_bounds`: current and allowed next phases for relationship pairs.
- `knowledge_locks`: facts that must remain unknown or unconfirmed.
- `required_evidence_in_draft`: exact required beats that must appear in prose.
- `ending_target`: the required final turn, image, decision, or discovery.
- `packet_budget_chars`: maximum packet size.

Validation rules:

- Every thread or relationship state change claimed by a card must be listed in
  this chapter's contract.
- `allowed_to` and `forbidden_to` must not contain the same thread state.
- `allowed_moves` and `forbidden_moves` must not contain the same relationship
  state.
- Every `must_satisfy` item must appear in the packet.
- `ending_target` must be carried into the packet.
- Every `required_evidence_in_draft` string must appear in the final draft.
- A lock may be removed from a thread only when the removed lock appears in
  `allowed_reveals`.
