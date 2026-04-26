import pytest
from to_test import *

def test_analyze_orders_zero_items():
    result = analyze_orders(25, 0, 50.0)
    assert result == "empty_order"

def test_analyze_orders_no_items():
    result = analyze_orders(age=25, items=0, total=50.0)
    assert result == "empty_order"

# Sfarsitul implementarii testelor initiale existente.

def test_analyze_orders_single_item():
    result = analyze_orders(age=25, items=1, total=50.0)
    assert result == "accepted"

def test_analyze_orders_single_item_with_negative_total():
    with pytest.raises(ValueError):
        analyze_orders(age=25, items=1, total=-50.0)

def test_analyze_orders_single_item_with_zero_age():
    result = analyze_orders(age=0, items=1, total=50.0)
    assert result == "accepted"

def test_analyze_orders_single_item_with_negative_age():
    with pytest.raises(ValueError):
        analyze_orders(age=-5, items=1, total=50.0)

def test_analyze_orders_single_item_with_zero_total():
    result = analyze_orders(age=25, items=1, total=0.0)
    assert result == "accepted"
