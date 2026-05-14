import pytest
from to_test import *

def test_classify_delivery_light_weight():
    result = classify_delivery(3, 75, False)
    assert result == "light"

def test_classify_delivery_heavy():
    result = classify_delivery(6, 150, False)
    assert result == "heavy"

def test_classify_delivery_negative_weight():
    with pytest.raises(ValueError) as exc_info:
        classify_delivery(-1, 75, False)
    assert str(exc_info.value) == "Parametrii numerici nu pot fi negativi."

def test_classify_delivery_all_conditions_true():
    result = classify_delivery(4, 150, True)
    assert result == "special_handling"

def test_classify_delivery_no_else_if():
    result = classify_delivery(10, 250, True)
    assert result == "special_handling_long_route"

def test_classify_delivery_zero_distance():
    result = classify_delivery(5, 0, False)
    assert result == "light"

# Sfarsitul implementarii testelor initiale existente.
