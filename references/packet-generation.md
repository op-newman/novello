# Packet Generation

Packets are bounded Writer input. A packet translates the contract plus current
projections into enough scene context to write one chapter safely.

## Inputs

Read only:

1. `contracts/<id>.json`
2. `plans/chapters/<id>.json`
3. `story_bible.json`
4. `style_guide.md`
5. `projections/entities.current.json`
6. `projections/relationships.current.json`
7. `projections/threads.current.json`
8. `projections/obligations.open.json`
9. `projections/reader_memory.current.json`

Do not include whole old chapters. Include an old-prose excerpt only when the
contract or plan requires exact wording; cap each excerpt at 800 characters and
include at most 3 excerpts.

## Selection Rules

Include only facts that affect this chapter:

- opening location, immediate pressure, and scene setup,
- active entities in the plan, contract, obligations, or allowed moves,
- current relationship phases for bounded pairs,
- current thread states for allowed, overdue, or locked threads,
- knowledge limits and forbidden reveals,
- resolve-now and avoid-contradiction obligations,
- 2-4 style points relevant to this chapter's mood and POV,
- exact ending target.

Do not include:

- full histories,
- inactive thread background,
- relationship history beyond current phase and allowed next phase,
- worldbuilding that will not be used in this chapter,
- future plans beyond the contract.

## Compression Order

If the packet exceeds `contract.packet_budget_chars`, compress in this order:

1. Remove inactive thread background.
2. Compress entity entries to current location, knowledge, limits, and goal.
3. Compress reader memory to active promises only.
4. Reduce style focus to the 2 most relevant points.
5. Remove old-prose excerpts unless exact wording is required.

Never remove `must_do`, `must_not_do`, `relationship_bounds`,
`knowledge_limits`, `resolve_now` obligations, or `ending_target`.

## Mapping

- `contract.must_satisfy` -> `must_do` or `obligations`
- forbidden reveals and locks -> `must_not_do` and `knowledge_limits`
- `allowed_thread_moves` -> `active_threads`
- `relationship_bounds` -> `relationship_bounds`
- open obligations -> `obligations`
- plan scenes/entities -> `active_entities`
- `contract.ending_target` -> `ending_target`

When evidence is weak or a projection field is missing, write conservative
instructions instead of inventing detail.

## Validation

After writing `packets/<id>.json`, run:

```bash
python scripts/validate_packet.py --project-root <project_root> --chapter-id <id>
```

If validation fails, repair the packet once using only the validation errors and
the allowed inputs above. If it still fails, halt. Do not weaken the contract to
make packet validation pass unless the original contract was mechanically wrong.

## Output

Write `packets/<padded_id>.json` matching `packet-format.md`.

The packet should be readable by a Writer that knows nothing except the packet,
contract, chapter plan, and target length.
