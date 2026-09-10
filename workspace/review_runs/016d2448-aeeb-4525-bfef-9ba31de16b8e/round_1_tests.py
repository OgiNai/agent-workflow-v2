import pytest
from solution import calculate_average

def test_calculate_average_normal():
    assert calculate_average(10.0, 2) == 5.0
    assert calculate_average(5.0, 4) == 1.25

def test_calculate_average_zero_count():
    assert calculate_average(10.0, 0) == 0.0
    assert calculate_average(0.0, 0) == 0.0

def test_calculate_average_negative_values():
    assert calculate_average(-10.0, 2) == -5.0
    assert calculate_average(10.0, -2) == -5.0

def test_calculate_average_float_precision():
    assert calculate_average(1.0, 3) == 1.0 / 3.0

def test_calculate_average_invalid_types():
    with pytest.raises(TypeError):
        calculate_average("10", 2)
    with pytest.raises(TypeError):
        calculate_average(10.0, "2")