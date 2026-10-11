# The learning journal

This file describes the learner profile, the format of a journal entry, and the rules that keep the journal useful.

## Location

Keep one journal for each project, in `.recall/journal.md` at the root of the repository. Do not keep it in the folder of this skill: a skill installed for all projects would mix the weak spots of different codebases. Create the journal on the first run. It can be ignored by git.

## Learner profile

Start the journal with the profile:

```markdown
# Recall journal

Learning: C++20
Stronger language: Java
```

`Learning` is the main language of the codebase. `Stronger language` is the language that the user knows better. Ask the user for it one time for each project.

## Entry format

Append one entry for each session:

```markdown
## 2026-07-17 — topic: order pipeline
- ✅ knew: how a request reaches the handler, why validation runs first
- ❌ missed: why an order is looked up by id and not passed in (asked: ...)
- ❌ syntax: could not write the lambda capture unaided
- revisit: template argument deduction in the repository layer
```

## Rules

- Record the results for code that the user wrote by hand apart from the results for concepts. A user can explain a concept correctly and still not be able to type it. Use `❌ syntax:` for these misses.
- When the user answers a previous miss correctly in a later session, mark the old line `✅ (recovered)`.
- `scripts/journal.py review` reads `❌` and `revisit:` lines. Keep these prefixes exactly as shown.
