import pytest
from to_test import decide_maintenance


@pytest.mark.parametrize(
    "machine_age,operating_hours,error_count",
    [
        (-1, 0, 0),
        (0, -1, 0),
        (0, 0, -1),
    ],
)
def test_validation_or_condition_rejects_each_negative_field(machine_age, operating_hours, error_count):
    with pytest.raises(ValueError):
        decide_maintenance(machine_age, operating_hours, error_count, False)


def test_zero_usage_cycles_do_not_add_scheduled_prefix():
    assert decide_maintenance(1, 999, 0, False) == "normal"


def test_five_usage_cycles_do_not_add_scheduled_prefix():
    assert decide_maintenance(1, 5000, 0, False) == "normal"


def test_six_usage_cycles_add_scheduled_prefix():
    assert decide_maintenance(1, 6000, 0, False) == "scheduled_normal"


def test_error_count_branch_selects_normal_or_inspect():
    assert decide_maintenance(1, 0, 0, False) == "normal"
    assert decide_maintenance(1, 0, 2, False) == "inspect"


def test_priority_or_condition_accepts_old_age_or_critical_sensor():
    assert decide_maintenance(10, 0, 0, False) == "normal"
    assert decide_maintenance(11, 0, 0, False) == "priority"
    assert decide_maintenance(1, 0, 0, True) == "priority"
