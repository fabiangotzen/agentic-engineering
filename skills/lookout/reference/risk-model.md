# Risk model

This file describes how a sighting scores one change, and how to tune it.

## Score

The change is the diff between its merge base and the working tree. The score is a weighted sum of five factors, each squashed to 0..1, times 100. Low is under 30, medium is 30 to 59, high is 60 and over.

| Factor | Weight | Value | Why |
| --- | --- | --- | --- |
| Hotspot exposure | 0.30 | Hotspot score of the hottest touched file divided by the top hotspot of the repository. | Defects already collect in the worst hotspot. |
| Complexity added | 0.25 | Sum over touched functions of `max(0, ccn_after - max(ccn_before, 10))`, divided by 30, capped at 1. | Only increases above a notable threshold count. |
| Change size | 0.20 | `log10(1 + changed source lines) / 3`, capped at 1. 1,000 lines saturate it. | Review quality drops sharply after a few hundred lines. |
| Missing test changes | 0.15 | `1 - test lines / source lines`, floored at 0. Test files are paths that contain `test` or `spec`. | Source changed without matching tests. |
| Spread | 0.10 | `(top-level areas touched - 1) / 4`, capped at 1. | A change across many areas is hard to understand as a whole. |

## Why these choices

- **Worst file, not the sum.** A sum saturates on every large change. The reviewer needs the riskiest file.
- **A complexity floor of 10.** Otherwise every feature with small new functions looks risky, and people learn to ignore the score.
- **Log-scaled size.** 10 to 100 lines matters much more than 1,000 to 1,100.
- **Relative hotspots.** In a small repository everything is a hotspot of something. The repository maximum keeps the factor useful at every size.

## Tuning

Tune against the history of the repository, not intuition.

1. Score the last fifty merged changes against their own bases.
2. Compare the scores with the changes that later needed a fix or a revert.
3. Change one weight at a time. Keep the sum of the weights at 1. Record the reason in the commit.
4. Set a factor to zero if it never separates good changes from bad. Do not keep it for show.

## Blind spots

- Lizard does not see configuration, schema and infrastructure changes. They score zero.
- A rename counts as one delete and one add.
- A change that only deletes code can still score medium on size. Read the factors, not only the number.
