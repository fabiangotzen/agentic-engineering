# Package mode

This file describes the package mode: an overview with sequence diagrams, a quiz in six levels, and a reviewer explanation.

## Rules

- Base every statement on the code. If you are not sure, say so.
- Keep answers short. No praise and no filler.
- Do not edit project files. Only the journal is written.
- Answer in the language of the user (German or English).

## Step 1: Overview

Read the code of the package first. Then write the answer in this order:

1. Max 10 lines: purpose, entry points, and the other packages it uses. Use real class names.
2. One sequence diagram for each entry point, max 2. Pick the most important entry points.
3. One line that starts with `Data flow:` and says what goes in and what comes out.
4. Ask the user if they want the quiz (step 2).

Do not explain line by line.

### Diagram format

Use plain ASCII in a code block. Do not use Mermaid.

```
Controller          OrderService        helpers         [DB]
    |---place(req)---->|                   |              |
    |                  |---validate(o)---->|              |
    |                  |<- - - boolean - - |              |
    |  +-- alt [valid] ------------------------------------+
    |  |               |---save(order)-------------------->|
    |  |               |<- - - - - - - - - Order - - - - - |
    |  +---------------------------------------------------+
    |<- - - Order - - -|
```

- Line 1 lists the participants, left to right in call order, separated by 2 or more spaces. Max 6.
- Participants are real classes.
- Put static-only utility classes into one `helpers` lifeline.
- Put external systems in brackets: `[DB]`, `[Kafka]`, `[SAP]`, `[REST]`.
- A call arrow `---name(args)--->` uses the real method name.
- A return arrow `<- - Type - -` is dashed and shows the return type.
- Use `loop` and `alt` frames only where they change the flow.

### Verify

Save the answer to a file in a temporary folder. Then RUN:

```
python <this skill's folder>/scripts/check_overview.py <answer file> --src <package folder>
```

Fix every line that it prints, then show the answer.

## Step 2: Quiz (only if the user says yes)

Ask one question at a time. Say the level, for example "Level 2/6". Before a new level, say in one sentence how it
connects to the previous level.

| Level | Topic            | Question                                                    | Why                          |
|-------|------------------|-------------------------------------------------------------|------------------------------|
| 1     | Purpose          | What problem does this package solve? What does it not do?  | Sets the boundaries.         |
| 2     | Structure        | What are the main classes and how do they relate?           | Builds a map before the flow.|
| 3     | Data flow        | Walk one request end to end.                                | Shows runtime behavior.      |
| 4     | Responsibilities | Why is each class here? Why these visibility choices?       | Shows design intent.         |
| 5     | Behavior         | Edge cases, invariants, expected outputs.                   | Tests detail.                |
| 6     | Change impact    | What breaks if we remove or change this?                    | Tests architecture.          |

- Do not ask level 4 before the user answered at least two questions on level 2 and two on level 3.
- If the user asks to skip a level, skip it.
- Say right, partly right, or wrong. Correct answers that are not precise.
- If wrong, give a hint that points to the code, not to the answer.
- Give the answer only after two failed tries, or when the user says "I give up".
- After each answer, name the file to open to check it.

## Step 3: Reviewer explanation

Start when the user says they are ready, or after level 5.

1. Ask the user to explain the package to a reviewer in 5 to 8 sentences.
2. List what is missing or wrong.
3. Give 3 things to try next.
