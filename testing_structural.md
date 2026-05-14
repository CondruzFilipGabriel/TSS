# Structural test instructions

Category instruction: create tests that force specific execution paths inside the function.
Structural tests target branches, compound conditions, loops, guards, assignments and return paths.
The assertion must still check visible behavior, but the chosen input should exercise a specific path.
If coverage reports missing lines, prefer tests that execute those missing lines.
When a loop affects the result, trace the loop manually before writing the expected value.
Each numbered line below is one direct instruction for one small pytest test.

1. Make one test that takes the if branch of an if-else statement.
2. Make one test that takes the else branch of an if-else statement.
3. Make one test that enters an input guard and raises the exact exception.
4. Make one test where the first part of an or input guard is True.
5. Make one test where the first part of an or input guard is False and the second part is True.
6. Make one test where all parts of a compound and condition are True and the branch body runs.
7. Make one test where the first part of a compound and condition is False and the branch body is skipped.
8. Make one test where the first part of a compound and condition is True but the second part is False and the branch body is skipped.
9. Make one test that enters a no-else if which changes a result computed earlier.
10. Make one test that skips a no-else if which would change a result computed earlier.
11. Make one test where a later no-else if replaces the result computed by an earlier branch.
12. Make one test where a later no-else if appends to or modifies the result computed earlier.
13. Make one test where a later no-else if does not change the result.
14. Make one test where a loop runs zero times.
15. Make one test where a loop runs exactly one time.
16. Make one test where a loop runs multiple times but does not trigger the later loop-based branch.
17. Make one test where a loop runs enough times to trigger the later loop-based branch.
18. Make one test exactly before a comparison boundary changes behavior.
19. Make one test at the first value after a comparison boundary changes behavior.
20. Make one test that reaches the final return after the longest normal execution path.
21. Make one test that reaches the same final return through a different execution path.
