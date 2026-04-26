# Initial tests

Goal:
Create one concrete pytest test function for the requested numbered rule.

Output:
- Return exactly one complete Python pytest test function.
- Start the function name with `test_`.
- Target only the provided source code.
- Use direct assertions or `pytest.raises`.
- Put only test logic inside the function.

Test construction:
- Implement the requested numbered rule exactly.
- Derive expected behavior from the provided source code and comments.
- Use concrete inputs supported by the current code.
- Select behavior reachable through normal function calls.
- Keep one primary purpose and one scenario.
- Prefer a meaningful uncovered area that still matches the rule.

Priorities:
1. Correctness and pytest validity.
2. Match the generated function to the requested rule.
3. Simplicity.

# New tests

Goal:
Create one concrete pytest test function that adds a genuinely new accepted rule in the category.

Output:
- Return exactly one complete Python pytest test function.
- Start the function name with `test_`.
- Target only the provided source code.
- Use direct assertions or `pytest.raises`.
- Put only test logic inside the function.

Search:
- Read the source code, accepted tests, rejected attempts, and category file.
- Select one category-specific area that seems insufficiently covered.
- Generate a category test that differs from accepted numbered rules and rejected attempts.

Test construction:
- Derive expected behavior from the provided source code and comments.
- Use concrete inputs supported by the current code.
- Select behavior reachable through normal function calls.
- Keep one primary purpose and one scenario.

Priorities:
1. Correctness and pytest validity.
2. Target an insufficiently tested area in the source code.
3. Propose a genuinely new rule.
4. Improve the testing score.
5. Keep it simple.

# Rule and reasoning

Goal:
Describe the accepted test as one reusable category rule.

Output:
- Return exactly two non-empty comment lines.
- Line one: `# Rule: <text>`
- Line two: `# Reasoning: <text>`

Rule construction:
- Write the type of test, not the concrete test data.
- Use the requested category vocabulary.
- Describe one generic situation tested by the accepted test.
- Use semantic terms instead of concrete values, names, return strings, or exception messages.
- Write the rule so it can guide a similar test for another function.

Rule text:
- Use plain English words.
- Use spaces and simple punctuation.
- Allowed punctuation: comma, period, semicolon, colon, and hyphen.
- Use category vocabulary as the main reference.

Reasoning construction:
- State what useful area the test adds.
- Keep it to one concise sentence.
