# Writer Protocol

Writer drafts chapter prose from bounded inputs. Writer must not browse or read
project files.

## Inputs

Pass only:

1. `packets/<id>.json`
2. `contracts/<id>.json`
3. `plans/chapters/<id>.json`
4. target length from `story_bible.json` or packet `target_length`

Do not pass projections, old chapters, logs, cards, or reviews.

## Task

Write Chinese chapter prose. Do not add a chapter heading unless the project
style requires one. Do not mention the contract, packet, or validation.

The draft must:

- satisfy every `must_do`,
- avoid every `must_not_do`,
- keep knowledge locks intact unless the contract allows the reveal,
- keep relationship movement within `relationship_bounds`,
- move threads only through allowed transitions,
- settle `resolve_now` obligations,
- preserve `avoid_contradiction` obligations,
- land on `ending_target`,
- avoid inventing future-relevant facts outside the packet.

Weak or incomplete packet facts must be written conservatively. Do not expand a
weak fact into new lore.

## Revision Budget

Writer may revise internally up to 2 times. The main agent may call Writer at
most 2 times total for one chapter. If a high/blocker issue remains after the
budget, halt.

## Output

Return exactly:

```text
DRAFT:
<full chapter prose>

SELF_CHECK:
- <packet item>: pass|fail - <short note>

CONTRACT_CHECK:
- <contract item>: pass|fail - <short note>

NEW_FACTS:
- <future-relevant fact introduced that was not in packet>
or
none

REVISION_COUNT: <0, 1, or 2>
```

`NEW_FACTS` is not a place for mood, metaphor, theme, or generic physical
description. List only concrete facts that may affect later chapters.

## Failure Severity

- `blocker`: illegal reveal, forbidden relationship leap, required obligation
  unresolved, ending target missed, or thread move outside contract.
- `high`: must-do omitted, unclear settlement of required beat, or new
  future-relevant fact that changes state without permission.
- `medium`: prose is mechanical, style drift, weak emotional causality, or
  scene lacks texture but contract passes.
- `low`: minor wording or pacing issue.
