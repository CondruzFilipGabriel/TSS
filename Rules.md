# Existing subtype test stage

Task: write exactly one pytest test for the requested instruction.

The requested instruction is the only testing goal for this answer.
Read the source code, choose concrete input values and write an exact assertion.

Output format:
- Return only one Python function.
- The function name must start with `test_`.
- Do not write imports.
- Do not write helper functions.
- Do not write markdown fences.
- Use the function from `to_test.py` directly.
- Use `assert` for returned values.
- Use `pytest.raises` for expected exceptions.
- Assert the exact visible behavior.

Behavior:
- Follow the requested instruction exactly.
- Use one concrete case.
- Use a new function name.
- Avoid repeating accepted tests.
- Avoid repeating rejected tests.
- Prefer simple inputs whose expected result is clear from the source code.

# New test discovery stage

Task: write exactly one new pytest test for the current category.

Use the category instruction as the main goal.
The new test must be different from the listed explicit subtypes and from already accepted or rejected tests.
Read the source code and choose a concrete behavior or execution path that is not already tested.

Output format:
- Return only one Python function.
- The function name must start with `test_`.
- Do not write imports.
- Do not write helper functions.
- Do not write markdown fences.
- Use the function from `to_test.py` directly.
- Use exact assertions.

Behavior:
- Do not repeat existing instructions.
- Do not repeat accepted tests.
- Do not repeat rejected tests.
- Prefer a test that can improve branch coverage or mutation score.
- Keep the test inside the current category.

# Rule synthesis stage

Task: write metadata for an accepted test.

Output format:
- Write one `# Rule:` line.
- Write one `# Reasoning:` line.
- The rule must be short, general and reusable.
- If there is no good reusable rule, write an empty rule.
