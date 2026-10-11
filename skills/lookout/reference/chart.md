# Chart

This file describes the chart: the dashboard that shows the terrain of one codebase.

## Terrain

The terrain is the current tree, measured. For each source file, it holds the size, the cyclomatic complexity of the worst function, and the churn. Churn is the number of commits that touch the file in a window. The default window is 90 days.

## What the chart is

The chart is one self-contained HTML page for this codebase. Generate it from git. Do not edit it by hand.

Build a chart for this codebase. Do not adapt a generic product to fit it.

Do not show one composite health score for the whole codebase. One number for "how good is this code" competes with the judgement of the people who know the code. One number is worse than no number. Show the measurements side by side, and let the trend show the direction.

## Panels

Start with these panels. Remove each panel that does not help.

| Panel | Content |
| --- | --- |
| Files by area | A treemap. Area is lines. Shade is the worst complexity. |
| Hotspots | Churn on x, complexity on y. Shade the quadrant where both are high. |
| Direction | One point for each merge to the main branch: functions over the complexity thresholds, the worst function, test lines per source line, cross-module dependencies. The trend is more important than one value. |
| Dependencies | The module graph, checked against the architecture rules that the repository already enforces. Draw a forbidden edge in red. |
| Ratchets | Each ratcheted number against its baseline. |

## Cost and freshness

Cache the measurements of each file by git blob id. Then the history over past merges costs one analysis for each changed file, not for each merge.

Render the page one time in CI, so that the chart cannot become out of date. Serve the page live during sessions, so that humans and agents see the same numbers.
