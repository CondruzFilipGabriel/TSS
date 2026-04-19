# Structural testing

Focus on execution structure.

Structural rules should target things such as:
- branches
- condition outcomes
- loop entry and loop exit
- zero, one, or multiple iterations
- distinct execution paths

A structurally new test must exercise a genuinely different execution path or control-flow outcome.
A different invalid input that reaches the same early validation path does not count as a new structural rule.

1. test a case that enters the loop zero times
