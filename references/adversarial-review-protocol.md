# Adversarial Review Protocol

Adversarial review is an optional, targeted second pass. It runs only for
high-risk chapters, not for every chapter. Its job is to attack the draft the
way a sharp reader would, so problems EditorReview waved through are caught
before they become committed truth in a card.

It is a literary and continuity gate, not a new canon store. It writes no cards
and no projections. Its findings fold into the existing `reviews/<id>.md`.

## When To Run

Run it when any of these holds:

- the contract sets `requires_adversarial_review: true` or `risk_level: high`,
- the chapter performs a major reveal or a relationship phase transition,
- EditorReview surfaced a `high` or `blocker` issue,
- the user asked for strict review.

If none hold, skip it. Do not add it to the default per-chapter flow.

## Inputs

Read only:

1. final draft from Writer,
2. `packets/<id>.json`,
3. `contracts/<id>.json`.

Do not read cards, projections, old chapters, or logs. The reviewer must judge
the draft against the same bounded context the Writer had, so a leak is visible
as a leak rather than excused by outside knowledge.

## Stance

Assume the draft has a hidden problem and try to find it. Do not rephrase the
draft's intent charitably. A clean pass is only credible after a real attempt to
break the chapter on these axes:

- **Knowledge leak**: does a character act on, hint at, or imply a fact that the
  packet's `knowledge_limits` or `must_not_do` keeps locked? Does narration leak
  a locked reveal through suggestive framing?
- **Voice drift**: compared to the packet `style_anchors`, has the POV loosened,
  the sentence rhythm changed, or the narration turned explanatory where it was
  restrained? Quote the drifting line.
- **Out of character**: does anyone act against established motivation only
  because the plot needs it? Is dialogue flattened into interchangeable voices?
- **Forgotten obligation**: is every packet obligation with `mode: resolve_now`
  or a `due_chapter` at or before this chapter actually paid off in the prose,
  not just mentioned?
- **Unearned transition**: if a relationship phase changes, is the emotional
  cause on the page, or does it rely on accumulated beats the reader never saw?

## Output

Return findings in the same shape EditorReview uses, so they merge cleanly:

```markdown
## Adversarial Findings
- severity: blocker|high|medium|low
  type: knowledge_leak|voice|ooc|obligation|relationship|reveal|new_fact
  evidence: "<short draft quote>"
  note: "<what is wrong and why it matters>"
  revision_instruction: "<one sentence>"

verdict: pass|revise|halt
```

## Decisions

- `halt`: a knowledge leak, an illegal reveal, or an unsettled due obligation.
  Stop before card extraction.
- `revise`: a fixable voice, OOC, or unearned-transition issue. The main agent
  may revise once if Writer budget remains.
- `pass`: only medium/low issues remain; log them in `reviews/<id>.md`.

The adversarial reviewer is still an AI pass, not a deterministic check. It
reduces blind spots; it does not replace the validators or human judgment on a
human checkpoint.
