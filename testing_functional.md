# Functional testing

Focus on observable behavior.

Functional rules should target things such as:
- returned results
- raised exceptions
- input validation
- behavior differences between input categories
- boundary situations with functional impact
- precedence between observable outcomes

A good functional rule must describe what the code visibly does for the caller: what it returns, what it raises, or what externally observable outcome it produces.
A functional rule must not be defined in terms of branches, loop counts, condition combinations, control-flow paths, or any internal execution structure.
A functionally new rule must be genuinely distinct from the other functional rules in this file and must not be only a narrower restatement, cosmetic variation, or concrete specialization of an existing rule.
A functionally new test should check a meaningfully different observable result, validation behavior, boundary effect, or observable priority between outcomes.

1. test a valid input case that should return the normal accepted result
2. Validate behavior for zero value inputs in analysis functions
3. Validate behavior for negative input values in analysis functions
4. New distinct accepted rule in this category
