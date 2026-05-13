# Structural test instructions

Category instruction: create tests that force specific execution paths inside the function.
A structural test chooses inputs to execute a targeted branch, compound-condition outcome, loop count, guard, assignment path or return path.
The test must still assert visible behavior, but its main goal is to cover internal control-flow paths.
Each numbered line below is one direct instruction for one small pytest test.

1. Make one test that executes the true branch of an if-else statement.
2. Make one test that executes the false branch of an if-else statement.
3. Make one test that enters an if statement that has no else.
4. Make one test that skips an if statement that has no else.
5. Make one test where the first side of an or condition is true.
6. Make one test where the second side of an or condition is true while the first side is false.
7. Make one test where every side of an and condition is true.
8. Make one test where the first side of an and condition is false.
9. Make one test where the second side of an and condition is false while the first side is true.
10. Make one test where a loop runs zero times.
11. Make one test where a loop runs exactly one time.
12. Make one test where a loop runs multiple times.
13. Make one test that reaches an exception raised by an input guard.
14. Make one test that reaches the final normal return.
15. Make one test where a later if changes a value produced earlier.
16. Make one test where a later if does not change a value produced earlier.
17. Make one test where a later condition appends or modifies the previously computed result.
18. Make one test where a compound condition is almost true but one part prevents the branch from running.
19. Make one test that reaches the same final return through a different branch path.
20. Make one test that distinguishes an exact comparison boundary from the next value after it.
