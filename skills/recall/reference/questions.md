# Writing questions

This file describes how to write the questions of a session, how to make the user write code, and how to grade that code.

## Question levels

Mix four levels in each session:

| Level | Example |
| --- | --- |
| Recall | "What does `InstallWorld` bind?" |
| Comprehension | "Why must renderers use `RenderTime()` instead of `GetTime()`?" |
| Prediction | "What happens if a unit test touches `WorldMap()` before it installs a world?" |
| Design | "Why do ally projectiles carry a string `kind` instead of a texture?" |

- Tie each language question to real lines. Use the places where the repository actually uses a feature, for example templates, const-correctness, value and reference parameters, resource lifetimes, or sum types.
- Show a real snippet and ask "What does this do?" or "What breaks if we change X?". Reading code is the skill that the session trains.
- Ask "Why is it designed this way?" more often than "What is it called?".

## Make the user write code

Reading code and writing code are different skills. In at least 2 of every 5 to 8 questions, the user must type real code in the reply.

- Do not accept a description in words where you asked for code. Say so warmly and ask again for the code.
- Make the task small and real: one line, one signature, or one blank in a real call.

Examples from a C++ codebase:

- "Type the line that sets the flame-strike cooldown to its maximum, with `def.cooldown`." (pointer-to-member `.*` syntax)
- "Write the signature of a function that changes a `GameState` and only reads an `InputFrame`." (`&` and `const &`)
- "Fill in the blank: `ForEachCooldown(state.cooldowns, ___);` so that it sets every cooldown to zero." (lambda syntax and capture list)
- "Rewrite `InteractableRef` as a `std::variant` and show the `std::visit` call."

## Grade the syntax

Grade the actual syntax, for example a missing `&`, a missing `const`, a wrong capture list, or `.` where `->` belongs. A quiz that only reads code hides these errors.

When the code is wrong, show the corrected line next to the line of the user. Name the specific rule.
