import pytest
from to_test import *

# Sfarsitul implementarii testelor initiale existente.

def test_analyze_orders_with_zero_items():
    with pytest.raises(ValueError):
        analyze_orders(25, 0, -1)

def test_analyze_orders_with_negative_age():
    with pytest.raises(ValueError):
        analyze_orders(-1, 5, 20)
