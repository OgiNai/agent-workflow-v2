from typing import Union

def div(a: Union[int, float], b: Union[int, float]) -> float:
    """Performs division and handles division by zero."""
    try:
        return float(a / b)
    except ZeroDivisionError:
        raise ValueError("The divisor 'b' cannot be zero.")
    except TypeError:
        raise TypeError("Both arguments must be numeric types.")