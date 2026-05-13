# This function evaluates a simple course result and returns a status string.
# It first validates that all numeric inputs are within their accepted ranges.
# Then it computes a limited homework bonus through a loop.
# After validation and score computation, it classifies the student:
# - scores of at least 50 are passed;
# - lower scores are failed;
# - weak attendance combined with a weak exam changes the status to at_risk;
# - very strong computed scores are marked as excellent.

def evaluate_course(attendance: int, homework_done: int, exam_score: int) -> str:
    """
    Returns a simple status for a course result.

    Rules:
    - attendance must be between 0 and 10
    - homework_done must be between 0 and 10
    - exam_score must be between 0 and 100
    - each completed homework gives one bonus point, up to a maximum of 5
    """

    # Validate the accepted input domain.
    # This compound condition is important because each invalid parameter must
    # trigger the same defensive behavior.
    if attendance < 0 or attendance > 10 or homework_done < 0 or homework_done > 10 or exam_score < 0 or exam_score > 100:
        raise ValueError("Parametrii sunt in afara intervalelor acceptate.")

    # Compute a capped homework bonus through a loop.
    # This loop is a useful mutation target because the cap, increment,
    # or number of iterations may be changed by a mutant.
    homework_bonus = 0
    for _ in range(homework_done):
        if homework_bonus < 5:
            homework_bonus += 1

    final_score = exam_score + homework_bonus

    # Apply the main pass/fail decision.
    # This if/else branch is central because it determines the default status.
    if final_score >= 50:
        status = "passed"
    else:
        status = "failed"

    # A student with low attendance and a weak exam is marked as at risk.
    # This is a compound condition without an else branch.
    if attendance < 5 and exam_score < 60:
        status = "at_risk"

    # Very strong results receive a more specific final classification.
    # This is a simple condition without an else branch.
    if final_score >= 95:
        status = "excellent"

    # Return the final classification after all rules have been applied.
    return status
