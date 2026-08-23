import pytest
from solution import div

def test_div_normal():
    assert div(10, 2) == 5.0
    assert div(5, 2) == 2.5
    assert div(-10, 2) == -5.0

def test_div_zero():
    with pytest.raises(ValueError, match="Division by zero is not allowed."):
        div(10, 0)

def test_div_invalid_types():
    with pytest.raises(TypeError, match="Both arguments must be numeric."):
        div("a", 2)
    with pytest.raises(TypeError, match="Both arguments must be numeric."):
        div(10, None)

def test_div_floats():
    assert div(10.5, 0.5) == 21.0

def test_div_large_numbers():
    assert div(1e10, 1e5) == 100000.0