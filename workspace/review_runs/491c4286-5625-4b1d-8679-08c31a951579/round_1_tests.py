import pytest
from solution import div

def test_div_integers():
    assert div(10, 2) == 5.0

def test_div_floats():
    assert div(5.5, 2.0) == 2.75

def test_div_negative():
    assert div(-10, 2) == -5.0

def test_div_zero_divisor():
    with pytest.raises(ValueError, match="The divisor 'b' cannot be zero."):
        div(10, 0)

def test_div_invalid_types():
    with pytest.raises(TypeError, match="Both arguments must be numeric types."):
        div("10", 2)
    with pytest.raises(TypeError, match="Both arguments must be numeric types."):
        div(10, None)

def test_div_zero_numerator():
    assert div(0, 5) == 0.0