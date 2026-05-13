import pytest
from to_test import *

def test_classify_delivery_light_delivery():
    result = classify_delivery(3, 20, False)
    assert result == "light"

def test_classify_delivery_heavy_delivery():
    result = classify_delivery(6, 20, False)
    assert result == "heavy"

def test_classify_delivery_no_else():
    with pytest.raises(ValueError):
        classify_delivery(-1, 50, False)

def test_classify_delivery_zero_checkpoints():
    result = classify_delivery(0, 0, False)
    assert result == "light"

def test_classify_delivery_single_checkpoint():
    result = classify_delivery(5, 49, False)
    assert result == "light"

def test_classify_delivery_loop_multiple_times():
    result = classify_delivery(10, 200, False)
    assert result == "heavy_long_route"

# Sfarsitul implementarii testelor initiale existente.
