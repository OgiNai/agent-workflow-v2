import pytest
from solution import div

def test_div_positive_numbers():
    assert div(10, 2) == 5.0

def test_div_negative_numbers():
    assert div(-10, -2) == 5.0
    assert div(10, -2) == -5.0

def test_div_float_precision():
    assert div(1, 3) == pytest.approx(0.3333333333333333)

def test_div_zero_divisor():
    with pytest.raises(ValueError, match="The divisor 'b' cannot be zero."):
        div(10, 0)

def test_div_zero_numerator():
    assert div(0, 5) == 0.0

def test_div_large_numbers():
    assert div(1e10, 1e5) == 100000.0