import pytest
from to_test import *

def test_classify_delivery_valid_values():
    result = classify_delivery(3, 150, False)
    assert result == "light"

def test_classify_delivery_heavy_and_long():
    result = classify_delivery(10, 200, False)
    assert result == "heavy_long_route"

def test_classify_delivery_heavy_and_fragile():
    result = classify_delivery(10, 250, True)
    assert result == "special_handling_long_route"

def test_classify_delivery_negative_values():
    with pytest.raises(ValueError) as exc_info:
        classify_delivery(-1, 50, False)
    assert str(exc_info.value) == "Parametrii numerici nu pot fi negativi."

    with pytest.raises(ValueError) as exc_info:
        classify_delivery(10, -50, False)
    assert str(exc_info.value) == "Parametrii numerici nu pot fi negativi."

def test_classify_delivery_boundary_values():
    result = classify_delivery(5, 100, False)
    assert result == "light"

def test_classify_delivery_boundary_weight_above_limit():
    result = classify_delivery(6, 100, False)
    assert result == "heavy"

def test_classify_delivery_zero_values():
    result = classify_delivery(0, 0, False)
    assert result == "light"

# Sfarsitul implementarii testelor initiale existente.
