# Chapter Card Format

Cards are immutable structured events. They are the only structured truth source.

Required fields:

```json
{
  "schema_version": 1,
  "chapter_id": 21,
  "title": "",
  "summary": "",
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

Every event or change that affects future writing should include `evidence`:

```json
{
  "text": "顾砚舟把是否去顾家的选择权交还给林晚星。",
  "evidence": "顾砚舟说：“去不去顾家，你自己决定。”"
}
```

`events[]` items with `participants` or `location` mutate generated projections
and therefore must include `evidence`.

Thread event:

```json
{
  "thread_id": "thread:lin_father_old_case",
  "action": "advance",
  "from": "gu_surname_handler",
  "to": "old_archive_coordination_role",
  "still_locked": ["旧经手人具体身份", "事故责任", "事故真相"],
  "next_review_chapter": 24,
  "evidence": "第一项，岗位类别：旧档案协调链。"
}
```

Relationship change:

```json
{
  "pair": ["char:lin_wanxing", "char:gu_yanzhou"],
  "from": "strained_trust_over_gu_surname_record",
  "to": "limited_collaboration_with_returned_choice",
  "evidence": "顾砚舟说：“去不去顾家，你自己决定。”"
}
```

Obligations use stable ids. Resolve by `id`; keep `text` for human readability:

```json
{
  "obligations_in": [{"id": "obl:c021_touch_old_case", "status": "resolved"}],
  "obligations_out": [
    {
      "id": "obl:c022_keep_truth_locked",
      "text": "Keep the accident truth locked until chapter 24.",
      "mode": "avoid_contradiction",
      "due_chapter": 24
    }
  ]
}
```

Cards should be short but not vague. Only future-relevant information belongs
in a card.

Do not store review commentary, style notes, or full chapter summaries in cards.
Cards are evidence-backed state events, not literary analysis.

`must_satisfy` items are semantic goals; they may not appear verbatim in the
draft or card. Mechanical validators should require exact
`required_evidence_in_draft` strings and settled obligations, while
EditorReview judges whether semantic goals were dramatized.
