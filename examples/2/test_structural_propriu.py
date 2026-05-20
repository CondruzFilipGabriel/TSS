import pytest
from to_test import evaluate_course


def test_no_homework_iterations_keep_exam_score_unchanged_for_fail_branch():
    assert evaluate_course(8, 0, 49) == "failed"


def test_pass_boundary_is_reached_at_final_score_50():
    assert evaluate_course(8, 1, 49) == "passed"


def test_homework_loop_stops_increasing_bonus_after_five_iterations():
    assert evaluate_course(8, 5, 89) == "passed"
    assert evaluate_course(8, 10, 89) == "passed"


def test_at_risk_compound_condition_requires_both_low_attendance_and_weak_exam():
    assert evaluate_course(5, 0, 59) == "passed"
    assert evaluate_course(4, 0, 60) == "passed"
    assert evaluate_course(4, 0, 59) == "at_risk"


def test_excellent_boundary_is_95_after_bonus():
    assert evaluate_course(8, 4, 90) == "passed"
    assert evaluate_course(8, 5, 90) == "excellent"


@pytest.mark.parametrize(
    "attendance,homework_done,exam_score",
    [
        (-1, 0, 50),
        (0, -1, 50),
        (0, 0, -1),
    ],
)
def test_validation_or_condition_rejects_each_negative_field(attendance, homework_done, exam_score):
    with pytest.raises(ValueError):
        evaluate_course(attendance, homework_done, exam_score)
