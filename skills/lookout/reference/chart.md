# Chart

This file describes the chart: the dashboard that the lookout keeps for one codebase.

## Rules

- The chart is one self-contained HTML page, generated from git. Do not edit it by hand.
- Build it for this codebase. Do not adapt a generic product.
- Do not show one composite health score. One number competes with the judgement of the people who know the code, and is
  worse than no number. Show the measurements side by side and let the trend show the direction.
- Each file has its size, the cyclomatic complexity of its worst function, and its churn: the commits that touch it in a
  window, 90 days by default.

## Data

`survey --json` gives the totals and the top hotspots only. Build the rest yourself: every file's measurements, the
history over merges, and the module dependencies.

## Panels

Start with these panels. Remove each panel that does not help.

| Panel         | Content                                                                                                                                                                                             |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Files by area | A treemap. Area is lines. Shade is the worst complexity.                                                                                                                                            |
| Hotspots      | Churn on x, complexity on y. Shade the quadrant where both are high.                                                                                                                                |
| Direction     | One point per merge to the main branch: functions over the complexity thresholds, the worst function, test lines per source line, cross-module dependencies. The trend matters more than one value. |
| Dependencies  | The module graph, checked against the architecture rules of the repository. Draw a forbidden edge in red.                                                                                           |
| Ratchets      | Each ratcheted number against its baseline.                                                                                                                                                         |

## Cost and freshness

- Cache each file's measurements by git blob id, so history costs one analysis per changed file, not per merge.
- Render the page in CI so it cannot go stale. Serve it live during sessions so humans and agents see the same numbers.
