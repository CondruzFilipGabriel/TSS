# Existing subtype test stage

Task: write exactly one pytest test for the requested instruction.

The requested instruction is the only goal for this answer.
Treat it as a command, not as a topic.
Read the source code, choose concrete input values and write the exact expected result.
If a loop affects the result, trace the loop before writing the assertion.

Output format:
- Return only one Python function.
- The function name must start with `test_`.
- Do not write imports.
- Do not write helper functions.
- Do not write markdown fences.
- Use the function from `to_test.py` directly.
- Use `assert` for returned values.
- Use `pytest.raises` for expected exceptions.
- Assert exact visible behavior.

Behavior:
- Follow only the requested instruction.
- Use one concrete case.
- Use a new function name.
- Do not repeat accepted tests.
- Do not repeat rejected tests.
- Prefer simple inputs with a clear expected result.

# New test discovery stage

Task: write exactly one new pytest test for the current category.

Use the category instruction as a requirement.
The new test must belong to the current category.
The new test must be different from the listed subtypes and from accepted or rejected tests.
Read the source code and choose one concrete behavior or execution path that is not already tested.
For functional tests, focus on visible behavior: returned values, exceptions, boundaries, flags and output classes.
For structural tests, focus on execution paths: branches, compound conditions, loops, guards, assignments, missing lines and return paths.

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
