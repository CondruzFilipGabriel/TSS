# Functional test instructions

Category instruction: create tests for visible behavior only.
Functional tests check what the caller can observe: exact returned values or exact raised exceptions.
Use normal inputs, invalid inputs, boundaries, flags and distinct output classes.
Do not target internal implementation details directly.
Each numbered line below is one direct instruction for one small pytest test.

1. Make one test with normal valid values and assert the exact returned result.
2. Make one test with different normal valid values and assert a different exact returned result.
3. Make one test with invalid numeric values and assert the exact exception.
4. Make one test with an invalid type or invalid shape, only if the function visibly rejects it.
5. Make one test with a value exactly on an important boundary and assert the exact returned result.
6. Make one test with a value just below an important boundary and assert the exact returned result.
7. Make one test with a value just above an important boundary and assert the exact returned result.
8. Make one test where a boolean or flag argument is True and assert the exact returned result.
9. Make one test where a boolean or flag argument is False and assert the exact returned result.
10. Make one test that returns a special result and assert that exact result.
11. Make one test that almost returns the special result, but does not, and assert the exact returned result.
12. Make one test with zero or the smallest allowed value and assert the exact returned result.
13. Make one test with large valid values and assert the exact returned result.
14. Make one test with valid values that combine two visible rules and assert the final exact result.
15. Make one test with valid values that avoid a visible special rule and assert the normal exact result.
16. Make one test where two different valid inputs produce the same visible result and assert that result.
