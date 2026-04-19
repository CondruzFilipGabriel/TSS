import pytest
from to_test import *

def test_analyze_orders_zero_items():
    result = analyze_orders(age=25, items=0, total=50.0)
    assert result == "empty_order"

# Sfarsitul implementarii testelor initiale existente.

def test_analyze_orders_one_item():
    result = analyze_orders(age=25, items=1, total=50.0)
    assert result == "accepted"

def test_analyze_orders_negative_age():
    with pytest.raises(ValueError):
        analyze_orders(age=-1, items=1, total=50.0)

def test_analyze_orders_negative_items():
    with pytest.raises(ValueError):
        analyze_orders(age=25, items=-1, total=50.0)

def test_analyze_orders_age_and_total_correct():
    result = analyze_orders(age=25, items=1, total=150.0)
    assert result == "accepted"
