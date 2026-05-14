import pytest
from to_test import *

def test_classify_delivery_valid_values():
    result = classify_delivery(3, 150, False)
    assert result == "light"

def test_classify_delivery_different_values():
    result = classify_delivery(10, 200, False)
    assert result == "heavy_long_route"

def test_classify_delivery_different_values_and_result():
    result = classify_delivery(3, 200, True)
    assert result == "special_handling_long_route"

def test_classify_delivery_negative_values():
    with pytest.raises(ValueError) as exc_info:
        classify_delivery(-1, 150, False)
    assert str(exc_info.value) == "Parametrii numerici nu pot fi negativi."

    with pytest.raises(ValueError) as exc_info:
        classify_delivery(3, -150, False)
    assert str(exc_info.value) == "Parametrii numerici nu pot fi negativi."

def test_classify_delivery_above_boundary_value():
    result = classify_delivery(6, 150, False)
    assert result == "heavy"

def test_classify_delivery_zero_values():
    result = classify_delivery(0, 0, False)
    assert result == "light"

def test_classify_delivery_same_result_different_inputs():
    result1 = classify_delivery(5, 100, False)
    result2 = classify_delivery(5, 150, False)
    assert result1 == "light"
    assert result1 == result2

# Sfarsitul implementarii testelor initiale existente.
