# Sources

This file lists where each idea in lookout comes from. Read the originals before you tune anything.

The hotspot analysis is the work of Adam Tornhill. Credit it as his.

| Idea                                                                       | Source                                                                                                                                                                 |
|----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Hotspots: change frequency times complexity                                | Adam Tornhill, *Your Code as a Crime Scene*, Pragmatic Bookshelf (2015; 2nd ed. 2024)                                                                                  |
| Function-level hotspots, change coupling, debt ranked by where work lands  | Adam Tornhill, *Software Design X-Rays*, Pragmatic Bookshelf (2018); tools: [code-maat](https://github.com/adamtornhill/code-maat), [CodeScene](https://codescene.com) |
| Churn predicts defects                                                     | Nagappan and Ball, "Use of Relative Code Churn Measures to Predict System Defect Density", ICSE 2005                                                                   |
| Cyclomatic complexity, the script's measure                                | Thomas J. McCabe, "A Complexity Measure", IEEE TSE SE-2(4), 1976; analyser: [lizard](https://github.com/terryyin/lizard)                                               |
| Cognitive complexity, closer to readability; add it where tools support it | G. Ann Campbell, "Cognitive Complexity", SonarSource white paper                                                                                                       |
| Instability, I = Ce / (Ca + Ce), for the dependency panel                  | Robert C. Martin, "OO Design Quality Metrics" (1994); *Agile Software Development* (2002)                                                                              |
| Baseline: record where the code is, fail only when it gets worse           | [betterer](https://github.com/phenomnomnominal/betterer)                                                                                                               |
| Keep reviews to a few hundred lines; basis of the log size factor          | Jason Cohen, *Best Kept Secrets of Peer Code Review*, SmartBear (2006)                                                                                                 |
