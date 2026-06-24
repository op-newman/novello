# Packet Format

The packet is the only context passed to Writer.

Required fields:

```json
{
  "schema_version": 1,
  "chapter_id": 22,
  "contract_id": "000022",
  "opening_state": "",
  "must_do": [],
  "must_not_do": [],
  "active_entities": [],
  "active_threads": [],
  "relationship_bounds": {},
  "knowledge_limits": {},
  "obligations": [],
  "style_focus": [],
  "old_prose_excerpts": [],
  "ending_target": "",
  "target_length": "3000-4000 Chinese characters"
}
```

Rules:

- Keep packet under `contract.packet_budget_chars`.
- Include every `contract.must_satisfy` item in `must_do` or another explicit
  packet field.
- Carry `contract.ending_target` into `ending_target`.
- Carry every `contract.relationship_bounds` key into `relationship_bounds`.
- Include every open obligation with `mode: resolve_now` or `avoid_contradiction`.
- Prefer stable obligation `id` values over free-text matching.
- Include high-priority overdue threads.
- Include all locks that would be dangerous to reveal.
- Include entity states only when they affect this chapter.
- Do not include full old chapters unless the contract requires exact wording.
- `old_prose_excerpts` is optional and capped at 3 short excerpts. Use it only
  for exact wording required by the contract or chapter plan.
