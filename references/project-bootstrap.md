# Project Bootstrap

ProjectBootstrap turns a loose novel idea into a runnable Novello project. It is
a creative conversation first and a file-writing step last.

Use this protocol when the user says things like:

- "Let's write a new novel."
- "Help me develop a novel idea."
- "Create a Novello project."
- "Turn this premise into a novel project."
- "Let's define the setting / outline / first chapter."

Do not enter the chapter-writing pipeline until the project has enough front
matter to support contracts and packets.

## Principles

- Do not start with a form. Start with the user's creative energy.
- Offer options and taste. Help the user compare directions.
- Ask at most 1-3 focused questions at a time.
- Do not write project files during exploration.
- Do not freeze a vague idea too early.
- Materialize files only after the user confirms the project brief.
- Keep the resulting project small enough to revise.

## Phase 1: Explore

Goal: discover what kind of novel the user wants.

Ask from natural entry points, not a checklist. Useful entry points:

- genre or shelf,
- protagonist,
- central relationship,
- world or social pressure,
- a scene image,
- emotional flavor,
- taboo / thing to avoid,
- comparable works,
- reader promise.

When the user gives a rough idea, propose 2-4 directions with tradeoffs. Example:

```text
This can go three ways:
1. High-pressure revenge thriller: fastest hook, darker tone.
2. Slow-burn romantic suspense: stronger relationship engine.
3. Workplace mystery: more grounded and serial-friendly.

I would lean toward 2 because your premise already has secrecy and emotional
pressure.
```

Explore output stays in conversation. Do not create files yet.

## Phase 2: Converge

Goal: turn exploration into a Project Brief that the user can approve or revise.

Produce a concise brief:

```markdown
## Project Brief

Title candidates:
- ...

Core promise:
...

Genre and reader experience:
...

Protagonist:
- desire:
- wound / flaw:
- pressure:
- initial agency:

Main relationship or opposition:
...

World rules and hard constraints:
- ...

Locked reveals:
- reveal:
  earliest_allowed_phase_or_chapter:
  why locked:

Major threads:
- id:
  current seed:
  expected rhythm:

First arc:
...

Chapter 1 seed:
- opening situation:
- must happen:
- must not reveal:
- ending hook:

Style direction:
...
```

Ask whether to revise or materialize. Do not write files until the user clearly
chooses to materialize.

## Phase 3: Materialize

Goal: write the initial project files.

Required user confirmation:

```text
Proceed with this brief and create the Novello project files?
```

If confirmed, create:

```text
novello.json
story_bible.json
style_guide.md
plans/global_plan.json
plans/arcs/arc_001.json
plans/chapters/000001.json
chapters/
contracts/
packets/
reviews/
cards/
projections/
logs/runs.jsonl
```

Then run:

```bash
python scripts/rebuild_projections.py --project-root <project_root> --write
```

With no cards, projections must be empty:

```text
entities.current.json = {}
relationships.current.json = {}
threads.current.json = {}
obligations.open.json = []
reader_memory.current.json = []
```

## Minimum File Content

`novello.json`:

```json
{
  "schema_version": 1,
  "title": "",
  "language": "zh-CN",
  "chapter_digits": 6
}
```

`story_bible.json` should capture the approved project brief: premise, genre,
reader promise, protagonist, main relationship/opposition, hard constraints,
world rules, locked reveals, and target length.

`style_guide.md` should capture voice, pacing, POV, dialogue, scene texture,
and things to avoid.

`plans/global_plan.json` should hold the long direction, major arcs, thread ids,
and reveal timing.

`plans/arcs/arc_001.json` should describe the first arc's promise, pressure,
turning points, and ending state.

`plans/chapters/000001.json` should include:

```json
{
  "schema_version": 1,
  "chapter_id": 1,
  "title": "",
  "goals": [],
  "required_reveals": [],
  "forbidden_reveals": [],
  "plot_threads_advanced": [],
  "ending_hook": "",
  "scenes": [],
  "style_notes": []
}
```

## Chapter 1 Rules

Chapter 1 starts from empty projections. It may create initial entities,
threads, relationship phases, knowledge states, locks, and obligations, but
only after the draft proves them and the card records evidence.

For chapter 1:

- no previous obligations exist,
- no previous relationship bounds exist unless specified in the approved brief,
- contract generation reads the approved front matter and empty projections,
- card extraction establishes the first structured truth.

## Halt Or Ask

Ask the user before materializing when:

- the core promise is still unclear,
- the protagonist's desire is missing,
- the main pressure or conflict is missing,
- the user has not chosen between materially different directions,
- writing files would overwrite an existing project.

Halt instead of writing files when:

- the target directory contains a different project,
- existing Novello files would be overwritten without explicit permission,
- required front matter cannot be inferred from the approved brief.
