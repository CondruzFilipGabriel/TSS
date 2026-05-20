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
def test_negative_numeric_inputs_are_rejected(machine_age, operating_hours, error_count):
    with pytest.raises(ValueError):
        decide_maintenance(machine_age, operating_hours, error_count, False)


def test_machine_without_errors_is_normal():
    assert decide_maintenance(2, 0, 0, False) == "normal"


def test_machine_with_errors_requires_inspection():
    assert decide_maintenance(2, 0, 1, False) == "inspect"


def test_old_machine_gets_priority_even_without_errors():
    assert decide_maintenance(11, 0, 0, False) == "priority"


def test_critical_sensor_gets_priority_even_for_new_machine():
    assert decide_maintenance(1, 0, 0, True) == "priority"


def test_many_usage_cycles_add_scheduled_prefix():
    assert decide_maintenance(2, 6000, 0, False) == "scheduled_normal"
