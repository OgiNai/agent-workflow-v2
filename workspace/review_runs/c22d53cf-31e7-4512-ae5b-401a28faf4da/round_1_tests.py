import pytest
from solution import calculate_average

def test_calculate_average_positive_integers():
    assert calculate_average(10, 2) == 5.0

def test_calculate_average_floats():
    assert calculate_average(10.5, 2.0) == 5.25

def test_calculate_average_zero_total():
    assert calculate_average(0, 5) == 0.0

def test_calculate_average_negative_numbers():
    assert calculate_average(-10, 2) == -5.0
    assert calculate_average(10, -2) == -5.0

def test_calculate_average_zero_count_raises_error():
    with pytest.raises(ValueError, match="Count cannot be zero when calculating an average."):
        calculate_average(10, 0)

def test_calculate_average_invalid_types():
    with pytest.raises(TypeError):
        calculate_average("10", 2)
    with pytest.raises(TypeError):
        calculate_average(10, None)