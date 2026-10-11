---
name: lookout
description: Measures where code change and complexity meet, keeps quality ratchets in CI, and gives each pull request a risk score with its factors. Use when the user asks for hotspots, codebase health, a codebase dashboard, quality ratchets, or the risk of a pull request or branch.
---

# Lookout

## Purpose

AI agents add change faster than people can read it. The codebase drifts a little with every merge.

This skill shows that drift with three tools:

- The **terrain**: each source file, measured from git history and static analysis.
- **Ratchets**: quality numbers that can only stay level or improve.
- The **sounding**: the risk score of one change, so that reviewers know where to look first.

A **hotspot** is a file where churn and complexity meet. Its score is churn times complexity, each normalised to the maximum in the repository. Complex code that nobody changes is not a hotspot. Simple code that changes daily is not a hotspot. Defects and review cost collect in complex code that keeps changing.

A ratchet covers four numbers. Three are totals: functions over the critical complexity threshold, long functions and hotspot files. The fourth is the worst function in each file that is already over the threshold.

The skill measures. It does not judge. The numbers show where to look. A human decides what is wrong.

## Workflow: chart a codebase

Use this workflow when the user wants to see the terrain, or when the repository has no chart.

```
- [ ] 1. Survey the terrain
- [ ] 2. Build the chart
- [ ] 3. Set the ratchets
- [ ] 4. Stop
```

1. Run `survey`. Read the top hotspots. Describe each hotspot in the words of the domain, not as a path.
2. Build the chart. Fit its panels to the architecture rules and size limits of the repository.
   Use the survey JSON for the panels of the current tree. Do not measure the current tree again.
   Use the cached measurements for each merge for the direction panel.
3. Run `ratchet init`. Commit the baseline. Add `ratchet check` to CI, next to the tests.
4. Stop. Charting does not change production code.

## Workflow: take a sounding of a change

Use this workflow when the user gives a pull request or a branch, or asks how risky a change is.

```
- [ ] 1. Run the sounding
- [ ] 2. Post the report
- [ ] 3. Add the action paragraph
- [ ] 4. Recommend, do not decide
```

1. Run `risk` against the base branch of the change.
2. Post the Markdown report. Always post all factors with the score.
3. Add a short paragraph that a human can act on. Name the files to read first, and give the reason. Name the ratchets that slipped. Name the hotspot that the change makes worse.
4. Do not approve or reject a change because of its score. Recommend where to look. The sounding orders review attention and never blocks a merge. Only ratchets fail a build.

## Workflow: after a cleanup session

1. Run `ratchet tighten`.
2. Compare the direction panel of the chart before and after the session.
3. If a hotspot cooled down, name the hotspot and say by how much its score dropped.

## Workflow: a ratchet slipped

1. Bring the number back. Split the function or simplify the branch.
2. Do not loosen the baseline.
3. Let a human decide to loosen a ratchet. Record that decision in the commit message.

## Reference files

- Before you build or change the chart, read [reference/chart.md](reference/chart.md).
- Before you tune the risk weights or explain a score, read [reference/risk-model.md](reference/risk-model.md).
- Read [reference/sources.md](reference/sources.md) once, before you credit the method or write about hotspots.

## Scripts

RUN `scripts/lookout.py`. It needs git, Python 3 and the `lizard` package. Install the package with `pip install lizard`.

| Command | Result |
| --- | --- |
| `scripts/lookout.py survey` | Prints the totals and the top hotspots. Add `--json` to get the same data for a dashboard or another agent. |
| `ratchet init` | Writes the baseline to `.lookout/ratchets.json`. Commit this file. |
| `ratchet check` | Fails when a ratcheted number got worse. |
| `ratchet tighten` | Lowers the baseline to the current numbers. Refuses while a ratchet has slipped. |
| `scripts/lookout.py risk --base origin/main --markdown` | Prints the score, every factor, the slipped ratchets and the files to review first. The output is ready for a pull request comment. |
