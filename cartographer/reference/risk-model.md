# Risk model

This file describes how the sounding calculates the risk score of one change, and how to tune it.

## Score

A sounding is the risk score of one change. The change is the diff between its merge base and the working tree. The score is a weighted sum of five factors, times 100. Each factor is squashed to 0..1.

The level is low under 30, medium from 30 to 59, and high from 60.

| Factor | Weight | Value | Why it matters |
| --- | --- | --- | --- |
| Hotspot exposure | 0.30 | The hotspot score of the hottest touched file, divided by the top hotspot of the repository. Touching the top hotspot gives 1. | Touching the worst hotspot touches the place where defects already collect. |
| Complexity added | 0.25 | Sum over touched functions of `max(0, ccn_after - max(ccn_before, 10))`, divided by 30, capped at 1. | Only increases above a notable threshold count. Trivial functions are noise. |
| Change size | 0.20 | `log10(1 + changed source lines) / 3`, capped at 1. 1,000 changed lines saturate the factor. | Review quality drops sharply after a few hundred lines. |
| Missing test changes | 0.15 | `1 - test lines / source lines`, floored at 0. Test files are paths that contain `test` or `spec`. | The source changed without matching test changes. |
| Spread | 0.10 | `(top-level areas touched - 1) / 4`, capped at 1. | One change across many top-level areas is difficult to understand as a whole. |

## Reasons for these choices

- **Worst file, not the sum.** A sum of exposure saturates on every large change. The reviewer needs to know the riskiest file.
- **A floor of 10 on complexity.** New code contains many small functions. If their complexity counts, every feature looks risky, and people learn to ignore the score.
- **Log-scaled size.** The difference between 10 and 100 changed lines is much more important than the difference between 1,000 and 1,100.
- **Relative hotspots, not absolute hotspots.** In a small repository, everything is a hotspot of something. Normalising to the maximum of the repository keeps the factor useful at every size.

## Tuning

Tune against the history of the repository, not against intuition.

1. Take the last fifty merged changes.
2. Score each change against its own base.
3. Compare the scores with the changes that later needed a fix or a revert.
4. Change one weight at a time.
5. Keep the sum of the weights at 1.
6. Record the reason in the commit.
7. If a factor never separates good changes from bad changes, set its weight to zero. Do not keep it for show.

## Known blind spots

- Lizard does not see configuration, schema and infrastructure changes. They score zero.
- A rename counts as one delete and one add.
- A change that only deletes code can still score medium on size. Read the breakdown, not only the number.
