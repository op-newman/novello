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
review unless the packet already included an excerpt. The packet's
`style_anchors`, when present, are the voice baseline for this review.

## Review Criteria

Check:

- POV and voice match the style guide.
- Voice stays consistent with the packet `style_anchors`, when present. Flag
  drift only when the prose has actually shifted register (for example, from
  restrained to over-explained), not when normal scene variation or earned
  character growth changes the rhythm.
- Required beats are dramatized, not summarized as checklist items.
- Relationship movement stays inside the allowed phase and has emotional cause.
- Thread movement is visible to a reader.
- Forbidden reveals and knowledge locks remain protected.
- The ending target is clear and chapter-shaped.
- New facts do not enlarge future continuity beyond the contract.
- Scene texture supports the genre and pacing.
- Packet `non_canon_dramatic_guidance`, when present, improves dramatic shape
  without being converted into confirmed canon.

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
they can be logged. Do not mark the review `pass` while any high/blocker issue
remains.

## Optional Adversarial Review

EditorReview is a single pass and can miss subtle knowledge leaks, voice drift,
or out-of-character beats. For high-risk chapters, run a second independent pass
using `references/adversarial-review-protocol.md` before card extraction.

Trigger an adversarial pass when any of these holds:

- the contract sets `requires_adversarial_review: true` or `risk_level: high`,
- the chapter performs a major reveal or a relationship phase transition,
- EditorReview itself surfaces a `high` or `blocker` issue,
- the user asks for strict review.

Do not run it on every chapter. It is a targeted gate, not a default stage.
When it runs, fold its findings into the same `reviews/<id>.md` issues list.

## RetconScan

After EditorReview passes and before card extraction, run a compact RetconScan.
This is not a second literary review and must not expand into prose critique. It
only checks whether the draft created continuity risk outside the packet and
contract.

Append the result to `reviews/<padded_id>.md`:

```markdown
## RetconScan
- durable_new_fact: none|suspected|found - <short note>
- knowledge_leak: none|suspected|found - <short note>
- relationship_jump: none|suspected|found - <short note>
- obligation_change: none|suspected|found - <short note>
- new_reader_promise: none|suspected|found - <short note>

retcon_verdict: pass|revise|halt
```

Use `found` when the draft clearly creates or changes a durable fact, confirms a
locked fact, moves a relationship beyond the contract, resolves or alters an
obligation without permission, or plants a reader promise not represented in
the contract/packet. Use `suspected` when the wording could be read that way and
should be clarified before card extraction.

A reader promise directly required by `must_satisfy`, `ending_target`, or a due
obligation is not a RetconScan risk. Mark `new_reader_promise: none` and note
that card extraction should record it as an outgoing `reader_promise` when the
draft evidence supports it.

Decision rules:

- `pass`: all items are `none`, or only low-risk `suspected` items remain and
  they are logged as degraded assumptions.
- `revise`: a suspected/found issue can be removed without changing the allowed
  chapter movement.
- `halt`: a found issue is contract-relevant and cannot be removed without human
  direction or a regenerated contract.

A RetconScan with any `found` field may not use `retcon_verdict: pass`. If
RetconScan says `revise` or `halt`, the top-level review verdict must also be
`revise` or `halt`.

After writing the review and RetconScan, validate the structure:

```bash
python scripts/validate_review.py --project-root <project_root> --chapter-id <id>
```

If validation fails, repair the review format or halt. Do not proceed to card
extraction with a missing RetconScan field or invalid verdict.
