import pytest
from solution import calculate_average

def test_calculate_average_normal():
    assert calculate_average(10.0, 2) == 5.0
    assert calculate_average(100.0, 4) == 25.0

def test_calculate_average_zero_count():
    assert calculate_average(10.0, 0) == 0.0

def test_calculate_average_negative_values():
    assert calculate_average(-10.0, 2) == -5.0
    assert calculate_average(10.0, -2) == -5.0

def test_calculate_average_float_inputs():
    assert calculate_average(5.5, 2) == 2.75

def test_calculate_average_large_numbers():
    assert calculate_average(1e10, 2) == 5e9

def test_calculate_average_invalid_types():
    with pytest.raises(TypeError):
        calculate_average("10", 2)
    with pytest.raises(TypeError):
        calculate_average(10, "2")