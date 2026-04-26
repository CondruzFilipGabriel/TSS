# Functional testing

This category checks visible behavior for the caller.

Vocabulary:
observable behavior, input class, output class, validation behavior, validation exception, boundary effect, accepted range, rejected range, threshold value, zero value, empty input, normal outcome, special outcome, rejected outcome, cause effect relation, masked effect, observable precedence, final visible result.

Sub-category areas:
- Equivalence class: distinguishes behavior between meaningful input classes.
- Output class: targets a distinct returned result or exception.
- Validation behavior: checks whether input is visibly accepted or rejected.
- Boundary effect: checks behavior at or near a behavior-changing boundary.
- Empty or neutral input: checks visible behavior when useful input data is absent or neutral.
- Category alternative: checks a meaningful alternative of an input property.
- Feasible combination: checks input properties that work together to change the visible result.
- Cause effect relation: links input conditions to the visible effect they produce.
- Cause constraint: checks a cause that works alone, as an alternative, or together with another cause.
- Masked effect or observable precedence: checks which visible outcome prevails over another.
- Normal or special outcome: distinguishes typical accepted behavior from a distinct non-default result.
- Type, domain, collection, membership, or state-like effect: checks a supported input property that changes the visible result.

Rule style:
- Describe the relation between input and visible behavior.
- Use observable behavior vocabulary.
- Generalize concrete values as input class, boundary, range, threshold, outcome, or effect.
- Each new rule adds different observable behavior, validation behavior, boundary effect, output class, cause effect relation, or observable precedence.
- Different concrete values count when they create different visible behavior.

1. test a valid input case that should return the normal accepted result
