# Refactor a skill to Agent Skills best practices

Use this prompt to restructure an existing skill into a lean `SKILL.md`, on-demand `reference/` files and
`scripts/`, without adding or changing instructions. It runs in three phases and stops after the analysis,
so you decide every contradiction before anything is written.

Replace `___/SKILLS.md` with the path to the skill's `SKILL.md`. The lookout, probe and recall skills in this
repository were refactored with it.

---

Task: Refactor my skill to follow Agent Skills best practices

Input: `___/SKILLS.md`
Output: one skill folder (or several, see step 3) with this layout:

```
skill-name/
├── SKILL.md
├── reference/
│   └── <topic>.md
└── scripts/
    └── <task>.py
```

## Rules for the whole task

- Do not add new instructions. Only keep, move, merge, rewrite, or delete.
- Do not change the meaning of an instruction.
- Keep code, commands, paths, and tool names exactly as written.

## Phase 1: Analyze (do not write files)

1. Number every instruction (I1, I2, …) with its source line.
2. Find contradictions. For each one, show the conflicting IDs and text,
   option A, option B, and your recommendation with one reason.
3. Decide the scope: one skill or several. If the file covers unrelated jobs
   that a user would ask for separately, propose one skill per job.
4. Give every instruction exactly one class:
    - BODY: needed every time the skill runs.
      Test: "If I remove this, will the skill fail on a typical use?" Yes → BODY.
    - REFERENCE → <file>: needed only for some uses.
    - SCRIPT: deterministic or fragile (validation, formatting, conversion,
      exact command sequences). Replace the prose with a script and its command.
    - DELETE: give one reason: the model already knows it, duplicate of Ix,
      too vague to act on, too obvious, or out-of-date time-sensitive info.
5. Draft the frontmatter for each skill.

Output: one table (ID | original text | class | destination | reason),
the contradiction list, and the draft frontmatter.
**Stop here. Wait for my answers before Phase 2.**

## Phase 2: Write

6. Frontmatter:
    - `name`: max 64 characters; lowercase letters, numbers, and hyphens only. Prefer gerund form
      (e.g. `processing-invoices`).
    - `description`: max 1024 characters, third person. Sentence 1: what the
      skill does. Sentence 2: "Use when …" with the words a user would type.
7. SKILL.md body:
    - Max 1500 tokens.
    - Order: purpose → required workflow (numbered steps; a copyable checklist
      if 4+ steps) → links to reference files → scripts and their commands.
    - Each link says WHEN to read it, e.g.
      `Before you edit an existing invoice, read [reference/editing.md](reference/editing.md).`
    - Links go one level deep. Reference files do not link to other reference files.
8. Reference files: start with one sentence that states the scope.
   Add a table of contents to any file over 100 lines.
9. Scripts:
    - For each script, state if the agent must RUN it or READ it.
    - Handle errors in the script and print clear error messages.
    - Explain each constant whose value is not obvious from its name: units, compatibility limits, or
      surprising behaviour. Do not write a comment that only repeats the name.
    - List required packages and the install command.
10. Use forward slashes in all paths. Use fully qualified MCP tool names
    (`Server:tool_name`), if the skill uses MCP tools.
11. Output each file in full with its path as a heading, then the folder tree.

## Language: ASD-STE100

Apply to all prose, including the description. Key rules:

- Procedures: one instruction per sentence, imperative, max 20 words.
- Descriptive text: max 25 words per sentence, present tense.
- Active voice. One word for one meaning; use the same term every time.
- Write "Do X" / "Do not do X", not "you should" or "try to".
- Exempt: code, commands, paths, tool and product names.

## Phase 3: Verify

Report each check as PASS/FAIL with evidence. For checks a script can do,
write a separate checker script (not part of the skill), run it, and show
the output.

Structure:

- [ ] Every Phase 1 ID appears in exactly one destination or the delete list.
- [ ] No instruction appears in more than one file.
- [ ] Every contradiction is resolved as I chose.
- [ ] `name` and `description` pass the rules in step 6.
- [ ] SKILL.md body token count: ___ (≤ 1500).
- [ ] Every link resolves to an existing file; no reference file links onward.
- [ ] List any procedure sentence over 20 words.
- [ ] List every flagged meaning change.

Behavior:

- [ ] Write 3 prompts that SHOULD trigger the skill and 2 that should NOT.
  For each, explain how the description leads to the right decision.
- [ ] Write 3 evaluation scenarios (prompt + expected behaviors) that I can
  run against the old and new skill to compare them.
