import pytest
from to_test import evaluate_course


@pytest.mark.parametrize(
    "attendance,homework_done,exam_score",
    [
        (-1, 0, 50),
        (11, 0, 50),
        (5, -1, 50),
        (5, 11, 50),
        (5, 0, -1),
        (5, 0, 101),
    ],
)
def test_invalid_values_are_rejected(attendance, homework_done, exam_score):
    with pytest.raises(ValueError):
        evaluate_course(attendance, homework_done, exam_score)


def test_homework_bonus_can_turn_borderline_result_into_passed():
    assert evaluate_course(8, 5, 45) == "passed"


def test_homework_bonus_is_capped_at_five_points():
    assert evaluate_course(8, 10, 44) == "failed"


def test_low_attendance_and_weak_exam_are_at_risk_even_after_passing_score():
    assert evaluate_course(4, 5, 59) == "at_risk"


def test_very_high_final_score_is_excellent():
    assert evaluate_course(8, 5, 90) == "excellent"
