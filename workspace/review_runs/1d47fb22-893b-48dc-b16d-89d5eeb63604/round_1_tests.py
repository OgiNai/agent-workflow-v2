import pytest
from solution import div

def test_div_positive_numbers():
    assert div(10, 2) == 5.0

def test_div_negative_numbers():
    assert div(-10, -2) == 5.0
    assert div(10, -2) == -5.0

def test_div_float_values():
    assert div(5.5, 2.0) == 2.75

def test_div_zero_denominator():
    with pytest.raises(ValueError, match="Division by zero is not allowed."):
        div(10, 0)

def test_div_zero_numerator():
    assert div(0, 5) == 0.0

def test_div_large_numbers():
    assert div(1e10, 1e5) == 100000.0