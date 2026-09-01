import pytest
from solution import div

def test_div_normal():
    assert div(10, 2) == 5.0
    assert div(5, 2) == 2.5

def test_div_negative():
    assert div(-10, 2) == -5.0
    assert div(10, -2) == -5.0
    assert div(-10, -2) == 5.0

def test_div_zero():
    assert div(10, 0) is None
    assert div(0, 0) is None

def test_div_floats():
    assert div(1.5, 0.5) == 3.0

def test_div_zero_numerator():
    assert div(0, 5) == 0.0