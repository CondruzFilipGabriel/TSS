# General directions for structural testing

Look for tests based on code structure and execution flow.

Search for:
- statements
- branches
- simple conditions
- compound conditions
- loops
- different important execution paths

Look for tests that exercise both outcomes of decisions when possible:
- true
- false

For compound conditions, look for tests that exercise different truth values of the individual conditions when possible.

Look for tests where changing one condition can change the final decision.

Pay special attention to:
- if with else
- if without else
- nested conditions
- loop entry
- zero iterations
- one iteration
- multiple iterations
- different loop exit cases

Prefer tests that exercise structurally different parts of the code.