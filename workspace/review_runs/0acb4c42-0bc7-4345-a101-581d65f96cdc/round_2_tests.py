import pytest
from solution import div

def test_div_positive_numbers():
    assert div(10.0, 2.0) == 5.0

def test_div_negative_numbers():
    assert div(-10.0, 2.0) == -5.0
    assert div(10.0, -2.0) == -5.0

def test_div_zero_divisor_raises_error():
    with pytest.raises(ValueError, match="The divisor 'b' cannot be zero."):
        div(10.0, 0.0)

def test_div_near_zero_divisor_raises_error():
    with pytest.raises(ValueError, match="The divisor 'b' cannot be zero."):
        div(10.0, 1e-10)

def test_div_floating_point_precision():
    assert div(1.0, 3.0) == 1.0 / 3.0

def test_div_zero_numerator():
    assert div(0.0, 5.0) == 0.0