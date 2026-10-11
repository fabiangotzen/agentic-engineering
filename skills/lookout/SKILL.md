---
name: lookout
description: Spots where code change and complexity meet, keeps quality ratchets in CI, and gives each pull request a risk score with its factors. Use when the user asks for hotspots, codebase health, a codebase dashboard, quality ratchets, or the risk of a pull request or branch.
---

# Lookout

## Purpose

AI agents add change faster than people can read it. The codebase drifts a little with every merge. A lookout watches ahead and calls out hazards early. This skill does that for a codebase:

- **Hazards** are hotspots: files where churn and complexity meet. The score is churn times complexity, each normalised to the repository maximum. Complex code that nobody changes is not a hazard, and neither is simple code that changes daily.
- **Ratchets** are quality numbers that only stay level or improve: functions over the critical complexity threshold, long functions, hotspot files, and the worst function in each file already over the threshold.
- A **sighting** is the risk score of one change. It tells reviewers where to look first.

Use the numbers to decide where to review first. A human decides what is wrong.

## Workflow: scan a codebase

Use when the user wants hotspots or the health of the codebase.

1. Run `survey`. Describe each top hotspot in the words of the domain, not as a path.
2. Stop. Scanning changes no files.

## Workflow: adopt lookout

Use only when the user asks for a chart, ratchets or a CI gate.

1. Build the chart. Fit its panels to the architecture rules and size limits of the repository. `survey --json` gives only the totals and the top hotspots: write the per-file listing, the history over merges and the dependency data yourself.
2. Run `ratchet init`. Commit the baseline. Add `ratchet check` to CI, next to the tests.
3. Do not change production code.

## Workflow: sight a change

Use when the user gives a pull request or a branch, or asks how risky a change is.

1. Run `risk` against the base branch of the change.
2. Post the Markdown report with all factors.
3. Add one paragraph that a human can act on: the files to read first and why, the slipped ratchets, and the hotspot that the change makes worse.
4. Recommend where to look. Do not approve or reject a change because of its score. Only ratchets fail a build.

## Workflow: after a cleanup

1. Run `ratchet tighten`.
2. Compare the direction panel before and after.
3. Name each hotspot that cooled down, and by how much.

## Workflow: a ratchet slipped

1. Bring the number back: split the function or simplify the branch.
2. Do not loosen the baseline. Only a human loosens a ratchet, with the reason in the commit message.

## Reference files

- Before you build or change the chart, read [reference/chart.md](reference/chart.md).
- Before you tune the risk weights or explain a score, read [reference/risk-model.md](reference/risk-model.md).
- Before you credit the method or write about hotspots, read [reference/sources.md](reference/sources.md).

## Scripts

RUN `scripts/lookout.py`. It needs git, Python 3 and `pip install lizard`.

| Command | Result |
| --- | --- |
| `survey [--json]` | The totals and the top hotspots. `--json` gives the data for the chart or another agent. |
| `ratchet init` | Writes the baseline to `.lookout/ratchets.json`. Commit it. |
| `ratchet check` | Fails when a ratcheted number got worse, or when there is no baseline. |
| `ratchet tighten` | Lowers the baseline to the current numbers. Refuses while a ratchet has slipped. |
| `risk --base origin/main --markdown` | The sighting: score, factors, slipped ratchets and files to review first, ready for a pull request comment. |
