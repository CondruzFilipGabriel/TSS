import pytest
from to_test import classify_delivery


def test_invalid_negative_weight_is_rejected():
    with pytest.raises(ValueError):
        classify_delivery(-1, 10, False)


def test_light_delivery_includes_weight_boundary():
    assert classify_delivery(5, 100, False) == "light"


def test_heavy_delivery_above_weight_boundary():
    assert classify_delivery(6, 100, False) == "heavy"


def test_fragile_delivery_over_100_km_needs_special_handling():
    assert classify_delivery(2, 101, True) == "special_handling"


def test_long_route_suffix_is_added_after_more_than_three_checkpoints():
    assert classify_delivery(6, 151, False) == "heavy_long_route"


def test_fragile_long_route_keeps_special_handling_and_adds_suffix():
    assert classify_delivery(2, 151, True) == "special_handling_long_route"
