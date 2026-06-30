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
  "style_anchors": [],
  "non_canon_dramatic_guidance": {
    "chapter_function": "",
    "primary_tension_to_dramatize": "",
    "subtext_to_suggest_not_confirm": [],
    "reader_experience_goal": "",
    "ending_effect_goal": ""
  },
  "old_prose_excerpts": [],
  "ending_target": "",
  "target_language": "zh-CN",
  "target_length": "3000-4000 characters"
}
```

Rules:

- Keep packet under `contract.packet_budget_chars`.
- Include every `contract.must_satisfy` item in `must_do` or another explicit
  packet field.
- Carry `contract.ending_target` into `ending_target`.
- Carry every `contract.relationship_bounds` key into `relationship_bounds`,
  including beat-only permissions such as `allowed_relationship_beats` and
  `forbid_phase_transition`.
- Include every open obligation with `mode: resolve_now` or `avoid_contradiction`.
- Include every obligation whose `due_chapter` is at or before this chapter, even
  when its mode is `maintain_pressure` or `background`. A due obligation must be
  settled this chapter, so the Writer needs it.
- Prefer stable obligation `id` values over free-text matching.
- Include high-priority overdue threads.
- Include all locks that would be dangerous to reveal.
- Include entity states only when they affect this chapter.
- Carry project language into `target_language`.
- Do not include full old chapters unless the contract requires exact wording.
- `old_prose_excerpts` is optional and capped at 3 short excerpts. Use it only
  for exact wording required by the contract or chapter plan.
- `style_anchors` is optional and capped at 3 entries. Each entry is an object
  with a non-empty `excerpt` under 400 characters: a short, recent draft sample
  that shows the voice the next chapter should hold. Refresh it roughly every
  five chapters. Use it as a voice reference for the Writer and a drift baseline
  for EditorReview, not as a source of plot facts. Do not derive numeric style
  metrics from it.
- `non_canon_dramatic_guidance` is optional and never a truth source. Use it to
  shape how the chapter reads, not to declare what has already happened. Keep
  it goal-shaped: write "test whether trust can hold under pressure", not "they
  now trust each other." Card extraction must ignore this field as evidence.
- `subtext_to_suggest_not_confirm` may name emotions, suspicions, or tensions to
  imply through behavior. It must not confirm locked facts, relationship phase
  changes, or durable character knowledge.
