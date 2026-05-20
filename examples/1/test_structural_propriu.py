import pytest
from to_test import classify_delivery


@pytest.mark.parametrize(
    "weight_kg,distance_km",
    [
        (-1, 0),
        (0, -1),
    ],
)
def test_each_negative_numeric_input_triggers_validation_branch(weight_kg, distance_km):
    with pytest.raises(ValueError):
        classify_delivery(weight_kg, distance_km, False)


def test_zero_distance_executes_no_checkpoint_iterations():
    assert classify_delivery(5, 0, False) == "light"


def test_three_checkpoints_do_not_trigger_long_route_branch():
    assert classify_delivery(5, 150, False) == "light"


def test_four_checkpoints_trigger_long_route_branch():
    assert classify_delivery(5, 151, False) == "light_long_route"


def test_fragile_condition_requires_fragile_flag_and_distance_over_100():
    assert classify_delivery(5, 101, False) == "light"
    assert classify_delivery(5, 100, True) == "light"
    assert classify_delivery(5, 101, True) == "special_handling"
