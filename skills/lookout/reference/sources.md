# Sources

This file lists the work that each idea in lookout comes from.

Lookout borrows every idea that it uses. Read the originals before you tune anything.

The hotspot analysis comes from Adam Tornhill. Credit it as his work.

## Hotspots and behavioural code analysis

- Adam Tornhill, *Your Code as a Crime Scene*, Pragmatic Bookshelf (2015; second edition 2024). Hotspot analysis combines change frequency from version control with a complexity measure. The book argues that the history of a codebase tells more than a snapshot.
- Adam Tornhill, *Software Design X-Rays*, Pragmatic Bookshelf (2018). Hotspots at function level, change coupling, and technical debt ranked by where the work lands.
- code-maat, the open-source tool of Adam Tornhill that mines version-control data: https://github.com/adamtornhill/code-maat
- CodeScene, the commercial product on the same ideas: https://codescene.com

## Churn as a defect predictor

- Nachiappan Nagappan and Thomas Ball, "Use of Relative Code Churn Measures to Predict System Defect Density", ICSE 2005. Relative churn predicted defect density in Windows Server 2003.

## Complexity measures

- Thomas J. McCabe, "A Complexity Measure", IEEE Transactions on Software Engineering, SE-2(4), 1976. Cyclomatic complexity, the measure that the script uses.
- G. Ann Campbell, "Cognitive Complexity: A new way of measuring understandability", SonarSource white paper. This measure is closer to how difficult code is to read. Add it to the chart where the tools support it.
- lizard, the language-agnostic analyser that the script runs: https://github.com/terryyin/lizard

## Dependencies

- Robert C. Martin, "OO Design Quality Metrics: An Analysis of Dependencies" (1994), and *Agile Software Development: Principles, Patterns, and Practices* (2002). Instability, I = Ce / (Ca + Ce), for the dependency panel.

## Ratchets

- betterer, a ratchet for incremental improvement in JavaScript and TypeScript projects: https://github.com/phenomnomnominal/betterer. It uses the same idea as the ratchets of the script. It records where the code is, and fails only when the code gets worse.

## Review size

- Jason Cohen, *Best Kept Secrets of Peer Code Review*, SmartBear (2006). This Cisco review study is the source of the common advice to keep reviews to a few hundred lines. The log scale of the change-size factor follows it.
