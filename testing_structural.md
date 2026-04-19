# Structural testing

Focus on execution structure.

Structural rules should target things such as:
- branches
- condition outcomes
- combinations of condition outcomes
- loop entry and loop exit
- zero, one, or multiple iterations
- distinct control-flow paths
- precedence between control-flow decisions

A good structural rule must describe how the code executes internally: which branch is taken, which condition outcome or condition combination is exercised, whether a loop is skipped or entered, or which distinct control-flow path is followed.
A structural rule must not be defined only in terms of returned values, raised exceptions, input categories, or other observable outcomes, unless those outcomes are used only as evidence for a distinct execution path.
A structurally new rule must be genuinely distinct from the other structural rules in this file and must not be only a narrower restatement, cosmetic variation, or concrete specialization of an existing rule.
A structurally new test should exercise a meaningfully different branch outcome, condition combination, loop behavior, or control-flow path.
A different input that reaches the same decisive path does not count as a new structural rule.

1. test a case that enters the loop zero times
2. New distinct accepted rule in this category
3. Ensure the function handles zero iterations in a loop correctly.
4. Ensure the function handles empty input gracefully.
