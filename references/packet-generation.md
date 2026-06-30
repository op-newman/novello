# Packet Generation

Packets are bounded Writer input. A packet translates the contract plus current
projections into enough scene context to write one chapter safely.

## Inputs

Read only:

1. `contracts/<id>.json`
2. `plans/chapters/<id>.json`
3. `novello.json`
4. `story_bible.json`
5. `style_guide.md`
6. `projections/entities.current.json`
7. `projections/relationships.current.json`
8. `projections/threads.current.json`
9. `projections/obligations.open.json`
10. `projections/reader_memory.current.json`

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
- every obligation whose `due_chapter` is at or before this chapter, regardless
  of mode, because it must be settled now,
- 2-4 style points relevant to this chapter's mood and POV,
- 1-3 `style_anchors` (short recent draft excerpts) when voice continuity is at
  risk, refreshed roughly every five chapters,
- optional `non_canon_dramatic_guidance` for chapter function, primary tension,
  suggested subtext, reader experience goal, and ending effect,
- exact ending target.

Do not include:

- full histories,
- inactive thread background,
- relationship history beyond current phase and allowed next phase,
- worldbuilding that will not be used in this chapter,
- future plans beyond the contract,
- dramatic guidance that states a durable fact, confirms a locked reveal, or
  declares a relationship/knowledge change as already true.

## Compression Order

If the packet exceeds `contract.packet_budget_chars`, compress in this order:

1. Remove inactive thread background.
2. Compress entity entries to current location, knowledge, limits, and goal.
3. Compress reader memory to active promises only.
4. Reduce style focus to the 2 most relevant points.
5. Reduce `style_anchors` to the single most representative excerpt.
6. Compress `non_canon_dramatic_guidance` to one short tension and one ending
   effect.
7. Remove old-prose excerpts unless exact wording is required.

Never remove `must_do`, `must_not_do`, `relationship_bounds`,
`knowledge_limits`, `resolve_now` obligations, any obligation due at or before
this chapter, or `ending_target`.

## Mapping

- `contract.must_satisfy` -> `must_do` or `obligations`
- forbidden reveals and locks -> `must_not_do` and `knowledge_limits`
- `allowed_thread_moves` -> `active_threads`
- `relationship_bounds` -> `relationship_bounds`, preserving beat-only limits
  such as allowed beat directions and phase-transition bans
- open obligations -> `obligations`
- plan scenes/entities -> `active_entities`
- `contract.ending_target` -> `ending_target`
- recent draft excerpts that fix the current voice -> `style_anchors`
- chapter function, dramatic pressure, subtext to suggest, and reader effect ->
  `non_canon_dramatic_guidance`
- `novello.json.language` or story-bible language -> `target_language`

When evidence is weak or a projection field is missing, write conservative
instructions instead of inventing detail.

`non_canon_dramatic_guidance` must be written as creative direction, not canon.
Prefer verbs like "test", "pressure", "suggest", "withhold", and "make the
reader feel" over state declarations like "is", "knows", "has become", or
"already trusts." If the guidance would require a new durable fact, put that
fact into the contract/plan path instead or omit it.

## Validation

After writing `packets/<id>.json`, run:

```bash
python scripts/validate_packet.py --project-root <project_root> --chapter-id <id>
```

Packet validation is a pre-draft check. It should read projections as they
exist before the target chapter card is written. If validating or auditing an
old packet after the target chapter exists, run:

```bash
python scripts/validate_packet.py --project-root <project_root> --chapter-id <id> --rebuild-as-of
```

`--rebuild-as-of` rebuilds packet validation memory from cards before the target
chapter, so a chapter is not blamed for obligations it created only after its
own packet was written.

If validation fails, repair the packet once using only the validation errors and
the allowed inputs above. If it still fails, halt. Do not weaken the contract to
make packet validation pass unless the original contract was mechanically wrong.

## Output

Write `packets/<padded_id>.json` matching `packet-format.md`.

The packet should be readable by a Writer that knows nothing except the packet,
contract, chapter plan, and target length.
