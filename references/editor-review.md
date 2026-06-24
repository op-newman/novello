# Editor Review

EditorReview is a literary gate. It protects reader experience and detects
contract-shaped prose that feels mechanical. It is not a second canon store.

## Inputs

Read only:

1. final draft from Writer,
2. `packets/<id>.json`,
3. `contracts/<id>.json`,
4. `plans/chapters/<id>.json`,
5. `style_guide.md`.

Do not read cards, projections, canon ledgers, or old chapters during the
review unless the packet already included an excerpt.

## Review Criteria

Check:

- POV and voice match the style guide.
- Required beats are dramatized, not summarized as checklist items.
- Relationship movement stays inside the allowed phase and has emotional cause.
- Thread movement is visible to a reader.
- Forbidden reveals and knowledge locks remain protected.
- The ending target is clear and chapter-shaped.
- New facts do not enlarge future continuity beyond the contract.
- Scene texture supports the genre and pacing.

## Output

Write `reviews/<padded_id>.md`:

```markdown
# Chapter <id> Review

## Verdict
pass|revise|halt

## Issues
- severity: blocker|high|medium|low
  type: voice|pacing|relationship|thread|reveal|obligation|ending|new_fact|style
  evidence: "<short draft quote or description>"
  note: "<what is wrong>"
  revision_instruction: "<one sentence>"

## Contract Experience
- <must_satisfy or bounded move>: satisfied|unclear|missing

## Notes
<brief editorial notes, no new canon>
```

## Decisions

- `pass`: proceed to card extraction.
- `revise`: the main agent may revise once if Writer budget remains.
- `halt`: stop before card extraction.

Use `halt` for illegal reveal, uncontracted relationship leap, missed
resolve-now obligation, or ending that contradicts the contract. Use `revise`
for fixable literary issues. Use `pass` when only medium/low issues remain and
they can be logged.
