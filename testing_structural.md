# Structural testing

This category checks executable structure.

Vocabulary:
statement area, guarded statement, branch outcome, decision outcome, atomic condition, compound decision, condition combination, condition influence, masked condition, short circuit behavior, loop skip, loop entry, repeated loop entry, loop exit, jump behavior, return point, exception point, execution path, path variation, default path, override path, linear sequence, control transfer.

Sub-category areas:
- Statement or guarded area: reaches code protected by a condition.
- Guarded continuation: passes early checks and reaches later logic.
- Decision or branch outcome: drives a feasible true, false, explicit, or implicit branch.
- Atomic condition: changes the truth value of one condition.
- Compound decision: exercises a meaningful combination of condition outcomes.
- Condition influence: shows that one condition changes the whole decision.
- Masked or short circuit condition: shows that one condition controls later evaluation or execution.
- Loop behavior: distinguishes loop skip, single entry, repeated entry, or normal exit.
- Loop internals: reaches a branch or control jump inside a loop.
- Early jump: reaches an early return or raise path.
- Return or exception point: reaches a distinct return or raise point.
- Sequential decisions: follows a meaningful ordered sequence of decisions.
- Override or default path: reaches a later override decision or the default execution path.
- Path variation: reaches a distinct feasible execution path.
- Linear sequence and control transfer: executes straight-line code followed by a distinct jump.
- Counter, accumulator, or traversal path: makes accumulated state or traversal affect a later decision.

Rule style:
- Describe execution structure.
- Use structural vocabulary.
- Describe the executed condition, branch, loop, jump, or path.
- Use observable assertions as evidence for the executed structure.
- Each new rule adds a different statement area, branch outcome, condition outcome, condition combination, loop behavior, jump behavior, condition influence, or feasible path.

1. test a case that enters the loop zero times
2. Exception point
3. Decision outcome based on atomic condition
4. Decision outcome based on masked or short circuit condition
