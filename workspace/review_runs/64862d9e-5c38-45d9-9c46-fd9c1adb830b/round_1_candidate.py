from typing import Union

def div(a: float, b: float) -> Union[float, None]:
    """Divides a by b, returning None if b is zero."""
    try:
        return a / b
    except ZeroDivisionError:
        return None