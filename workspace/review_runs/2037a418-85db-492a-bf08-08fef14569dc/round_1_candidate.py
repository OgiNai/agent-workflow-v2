from typing import Union

def div(a: float, b: float) -> float:
    """Divides two numbers and raises a ValueError if division by zero occurs."""
    if b == 0:
        raise ValueError("The divisor 'b' cannot be zero.")
    return float(a / b)