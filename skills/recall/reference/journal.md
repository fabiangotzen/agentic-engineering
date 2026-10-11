# The learning journal

This file describes the learner profile, the format of a journal entry, and the rules that keep the journal useful.

## Location

Keep the journal in `journal.md` in the folder of this skill. Create it on the first run. The journal can be ignored by git.

## Learner profile

Start the journal with the profile:

```markdown
# Recall journal

Learning: C++20
Stronger language: Java
```

`Learning` is the main language of the codebase. `Stronger language` is the language that the user knows better. Ask the user for it one time.

## Entry format

Append one entry for each session:

```markdown
## 2026-07-17 — topic: ability registry
- ✅ knew: dispatch flow, why a registry and not a switch
- ❌ missed: why AbilityDefinition is found by string id (asked: ...)
- ❌ syntax: could not write the .* assignment unaided
- revisit: template argument deduction in SkillTreeCore
```

## Rules

- Record the results for code that the user wrote by hand apart from the results for concepts. A user can explain a concept correctly and still not be able to type it. Use `❌ syntax:` for these misses.
- When the user answers a previous miss correctly in a later session, mark the old line `✅ (recovered)`.
- `scripts/journal.py review` reads `❌` and `revisit:` lines. Keep these prefixes exactly as shown.
