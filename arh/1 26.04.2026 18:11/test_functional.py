import pytest
from to_test import *

# Sfarsitul implementarii testelor initiale existente.

def test_analyze_orders_boundary_age():
    """
    Test that an order with age exactly at the boundary (18) is classified as accepted,
    even if the total is greater than 100.
    """
    result = analyze_orders(18, 5, 200)
    assert result == "accepted"

def test_analyze_orders_empty_items():
    """
    Test that an order with zero items is classified as 'empty_order',
    overriding any other potential status.
    """
    result = analyze_orders(20, 0, 50)
    assert result == "empty_order"

def test_analyze_orders_boundary_total():
    """
    Test that an order with total exactly at the boundary (100) is classified as accepted,
    even if the age is less than 18.
    """
    result = analyze_orders(17, 5, 100)
    assert result == "accepted"
