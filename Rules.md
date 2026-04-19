# Initial tests

* Return exactly one concrete Python pytest test function and nothing else.
* The test must target only the code from `to_test.py`.
* The test must implement exactly the requested rule from the given category.
* First priority is correctness and pytest validity against the provided source code.
* Second priority is rule relevance.
* Third priority is simplicity.
* Derive every expected result directly from the provided source code.
* Do not infer intended behavior beyond what is directly supported by the current code.
* If the requested rule is broad, choose one representative case that fits the rule reliably.
* Do not write imports, markdown, explanations, placeholders, helper code, or more than one function.

# New tests

* Return exactly one concrete Python pytest test function and nothing else.
* The test must target only the code from `to_test.py`.
* The test must belong to the requested category and embody a genuinely new rule in that category.
* The test is useful only if it is correct, valid under pytest, and improves the measured score when evaluated together with the current accepted tests of that category.
* First priority is correctness and pytest validity against the provided source code.
* Second priority is embodying a genuinely new rule in the requested category.
* Third priority is simplicity.
* Derive every expected result directly from the provided source code.
* Do not infer intended behavior beyond what is directly supported by the current code.
* If previous rejected attempts are shown, do not repeat them or make only cosmetic variations of them.
* Prefer a different observable behavior, branch outcome, condition outcome, loop behavior, or execution path from the already accepted tests and rejected attempts.
* Do not combine independent scenarios in the same test.
* Do not write imports, markdown, explanations, placeholders, helper code, or more than one function.

# Rule and reasoning

* Return only two comment lines and nothing else.
* The first line must be exactly in the form: `# Rule: <text>`
* The second line must be exactly in the form: `# Reasoning: <text>`
* The rule must be a general reusable testing rule written at the level of roles, relations, thresholds, boundaries, behaviors, or control-flow outcomes, not at the level of file-specific names or concrete values.
* Generalize semantically, not mechanically: describe the kind of situation and the expected behavior, using abstractions such as negative value, zero value, threshold value, below threshold, above threshold, default path, override path, validation path, compound condition true, or compound condition false when appropriate.
* The rule must fit the requested category: functional rules must describe observable behavior, while structural rules must describe execution structure such as branch outcomes, loop behavior, condition combinations, or distinct control-flow paths.
* The rule must be genuinely distinct from the existing rules of that category and must not be only a narrower restatement, cosmetic paraphrase, or concrete specialization of an already accepted rule.
* The rule must not contain concrete values, concrete strings, function names, variable names, class names, or other file-specific identifiers from the current script.
* The reasoning must briefly explain why this accepted test adds useful coverage or a genuinely new rule to the category.
* Do not return code, markdown, imports, explanations, or any extra text.
