import pytest
from solution import div

def test_div_integers():
    assert div(10, 2) == 5.0

def test_div_floats():
    assert div(5.5, 2.0) == 2.75

def test_div_negative():
    assert div(-10, 2) == -5.0
    assert div(10, -2) == -5.0

def test_div_zero_raises_error():
    with pytest.raises(ValueError, match="The divisor 'b' cannot be zero."):
        div(10, 0)

def test_div_zero_float():
    with pytest.raises(ValueError):
        div(10, 0.0)

def test_div_large_numbers():
    assert div(1e10, 1e5) == 100000.0

def test_div_type_consistency():
    assert isinstance(div(1, 2), float)