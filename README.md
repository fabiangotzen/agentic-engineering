# agentic

The skills, prompts and checks I use to build software with AI agents. Written and maintained by Fabian Gotzen.
More on the approach: https://www.fabiangotzen.net/agentic-engineering

## Contents

| Folder              | What is in it                                                                                            |
|---------------------|----------------------------------------------------------------------------------------------------------|
| [skills/](skills)   | Agent skills in the [Agent Skills](https://agentskills.io) layout: `SKILL.md`, `reference/`, `scripts/`. |
| [prompts/](prompts) | Prompts I reuse for multi-step work, each with a note on when to use it.                                 |
| [scripts/](scripts) | Local checks for this repository.                                                                      |

### Skills

| Skill                              | What it does                                                                                                                                       |
|------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| [integration-tests](skills/integration-tests/SKILL.md) | Writes and checks integration tests against real Testcontainers, with a Spring Boot setup, test data builders and a convention checker. |
| [lookout](skills/lookout/SKILL.md) | Spots where code change and complexity meet (hotspots), keeps a quality baseline in CI, and gives each pull request a risk score with its factors. |
| [probe](skills/probe/SKILL.md)     | Builds a headless text tool that drives an application through its real entry points and saves each session as a replayable action log.            |
| [recall](skills/recall/SKILL.md)   | Quizzes you on a codebase you own and its language, one question at a time, with code you write by hand, a journal of weak spots and a package walkthrough with sequence diagrams. |

Requirements: lookout needs git, Python 3 and `pip install lizard`. integration-tests, probe and recall need Python 3 only.

### Prompts

| Prompt                                        | Use it to                                                                                                               |
|-----------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| [refactor-agents](prompts/refactor-agents.md) | Split a long `AGENTS.md` into a short root index and task-specific files that agents load when needed.                  |
| [refactor-skill](prompts/refactor-skill.md)   | Restructure an existing skill into a lean `SKILL.md`, `reference/` files and `scripts/`, without changing what it says. |

## Install a skill

Copy a skill folder to where your agent loads skills, for example:

```
cp -r skills/lookout ~/.claude/skills/               # Claude Code, all projects
cp -r skills/probe <your-repo>/.claude/skills/        # Claude Code, one project
```

## Checks

```
python scripts/check_skills.py
```

Validates every skill: frontmatter limits, a `Use when` sentence, the body token budget, links that resolve,
reference files that do not link onward, and scripts that compile.

## Credits

The skills borrow their ideas and name their sources in each skill's `reference/sources.md`, among them Adam
Tornhill's hotspot analysis and deterministic simulation testing. Skills I use from others, such as
[Matt Pocock's](https://github.com/mattpocock/skills), stay in their own repositories.

## License

[MIT](LICENSE)
