# Refactor AGENTS.md for progressive disclosure

Refactor AGENTS.md for progressive disclosure: keep the root short and put task-specific instructions in files loaded
when needed.

Follow these steps:

1. **Find contradictions**: Identify any instructions that conflict with each other. For each contradiction, ask me
   which version I want to keep.

2. **Identify the essentials**: Extract only what belongs in the root AGENTS.md:
    - One-sentence project description
    - Anything truly relevant to every single task

3. **Group the rest**: Organize remaining instructions into logical categories. For each group, create a separate
   markdown file.

4. **Create the file structure**: Output:
    - A minimal root AGENTS.md serving as an index
    - Each file with its relevant instructions
    - A suggested docs/ folder structure

5. **Flag for deletion**: Identify any instructions that are:
    - Redundant, vague, or obvious

6. **Automate selectively**: If possible, automate the process and extract deterministic workflows.
    - Reuse existing scripts first. Extract a workflow into a script only when it is repeatable, deterministic, and
      useful beyond this refactor.

7. **Verify**:
    - Every retained instruction is accounted for without changing meaning.
    - Links and referenced paths resolve.
    - The root explains when each supporting file is needed.
    - No unresolved contradictions or unnecessary duplication remain.
    - Three representative tasks can find the guidance they need.
    - Any added scripts pass appropriate checks.
