# skills

Agent skills I use and maintain. Each folder is one skill in the [Agent Skills](https://agentskills.io) layout:
a `SKILL.md`, optional `reference/` files the agent reads on demand, and `scripts/` it runs or reads.

| Skill | What it does |
| --- | --- |
| [cartographer](cartographer/SKILL.md) | Charts where code change and complexity meet (hotspots), keeps quality ratchets in CI, and gives each pull request a risk score with its factors. |
| [probe](probe/SKILL.md) | Builds a headless text tool that drives an application through its real entry points and saves each session as a replayable action log. |

## Install

Copy a skill folder to where your agent loads skills, for example:

```
cp -r cartographer ~/.claude/skills/          # Claude Code, all projects
cp -r probe <your-repo>/.claude/skills/       # Claude Code, one project
```

## Requirements

- cartographer: git, Python 3 and `pip install lizard`
- probe: Python 3, no other packages

More on how I work with agents: https://www.fabiangotzen.net/agentic-engineering
