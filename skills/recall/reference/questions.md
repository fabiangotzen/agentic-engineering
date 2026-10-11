# Writing questions

This file describes how to write the questions of a session, how to make the user write code, and how to grade that
code.

## Question levels

Mix four levels in each session. Take every name in a question from the real code of the repository.

| Level         | Example                                                                                      |
|---------------|----------------------------------------------------------------------------------------------|
| Recall        | "What does `configure_routes` register?"                                                     |
| Comprehension | "Why does the handler read the time from an injected `Clock` and not from the system clock?" |
| Prediction    | "What happens if a test calls `OrderService.place` before the repository is set up?"         |
| Design        | "Why does an order event carry a product id and not the product object?"                     |

- Tie each language question to real lines. Use the places where the repository actually uses a feature, for example
  generics or templates, immutability, value and reference semantics, resource lifetimes, error handling, or sum types.
- Show a real snippet and ask "What does this do?" or "What breaks if we change X?". Reading code is the skill that the
  session trains.
- Ask "Why is it designed this way?" more often than "What is it called?".

## Make the user write code

Reading code and writing code are different skills. In at least 2 of every 5 to 8 questions, the user must type real
code in the reply.

- Do not accept a description in words where you asked for code. Say so warmly and ask again for the code.
- Make the task small and real: one line, one signature, or one blank in a real call.

Examples, each in the language of its codebase:

- C++: "Write the signature of a function that changes an `Order` and only reads a `Config`." (`&` and `const &`)
- C++: "Fill in the blank: `std::erase_if(orders, ___);` so that it removes every cancelled order." (lambda syntax and
  capture list)
- Python: "Write the `@dataclass` for `Refund` so that its fields cannot be reassigned." (`frozen=True`)
- TypeScript: "Write the type of `Result` so that the compiler forces the caller to handle the error case." (
  discriminated union)
- Java: "Rewrite this `if` chain over `Shape` as a `switch` over a sealed interface." (pattern matching)

## Grade the syntax

Grade the actual syntax, for example a missing `&` or `const`, a wrong capture list, a missing `await`, or a mutable
default argument. A quiz that only reads code hides these errors.

When the code is wrong, show the corrected line next to the line of the user. Name the specific rule.
