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
* If existing explicit rules are shown, the new rule must be genuinely distinct from them and must not be only a narrower restatement, cosmetic variation, or concrete specialization of an existing rule.
* If previous rejected attempts are shown, do not repeat them and do not make only cosmetic variations of them.
* Prefer a different observable behavior, validation behavior, branch outcome, condition outcome, loop behavior, or execution path from the already accepted tests, existing explicit rules, and rejected attempts.
* Do not combine independent scenarios in the same test.
* Do not write imports, markdown, explanations, placeholders, helper code, or more than one function.

# Rule and reasoning

* Return only two comment lines and nothing else.
* The first line must be exactly in the form: `# Rule: <text>`
* The second line must be exactly in the form: `# Reasoning: <text>`
* The rule must be a general reusable testing rule written at the level of roles, relations, thresholds, boundaries, behaviors, or control-flow outcomes, not at the level of file-specific names or concrete values.
* Generalize semantically, not mechanically: describe the kind of situation and the expected behavior using abstractions such as analyzed function, numeric parameter, counting parameter, state parameter, input data, parameter combination, zero value, unit value, threshold value, below the threshold value, above the threshold value, at the threshold value, minimum accepted value, minimum rejected value, maximum accepted value, maximum rejected value, accepted range, relevant range, accepted outcome, rejected outcome, special outcome, validation exception, observable behavior, boundary effect, validation path, default path, override path, simple condition, compound condition, execution path, loop entry, or loop exit.
* The rule must fit the requested category: functional rules must describe observable behavior, while structural rules must describe execution structure such as branch outcomes, loop behavior, condition combinations, or distinct control-flow paths.
* The rule must be genuinely distinct from the existing rules of that category and must not be only a narrower restatement, cosmetic variation, or concrete specialization of an already accepted rule.
* The rule must not contain digits, underscores, backticks, parentheses, brackets, braces, slashes, operator-like notation, function names, variable names, class names, concrete strings, concrete return values, or concrete instantiated values from the current script.
* If a concrete identifier or value would normally appear, replace it with a simple semantic abstraction from the vocabulary above.
* If the first formulation is too concrete, rewrite it in a more general form using the abstraction vocabulary above while preserving the testing meaning and the category-specific focus.
* The reasoning must briefly explain why this accepted test adds useful coverage or a genuinely new rule to the category.
* Do not return code, markdown, imports, explanations, or any extra text.