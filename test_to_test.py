from to_test import analyze_orders
import pytest

def test_valid_inputs():
    assert analyze_orders(18, 5, 200) == "accepted"
    assert analyze_orders(30, 0, 0) == "empty_order"

def test_invalid_inputs():
    with pytest.raises(ValueError):
        analyze_orders(-1, 5, 200)
    with pytest.raises(ValueError):
        analyze_orders(18, -1, 200)
    with pytest.raises(ValueError):
        analyze_orders(18, 5, -1)
