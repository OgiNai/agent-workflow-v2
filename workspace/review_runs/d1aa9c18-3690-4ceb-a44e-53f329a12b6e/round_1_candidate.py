from typing import Union

def div(a: float, b: float) -> float:
    """Divides two numbers and handles division by zero."""
    try:
        return float(a) / float(b)
    except ZeroDivisionError:
        raise ValueError("Division by zero is not allowed.")
    except (TypeError, ValueError):
        raise TypeError("Both arguments must be numeric.")