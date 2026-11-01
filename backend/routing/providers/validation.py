from routing.domain.units import nonnegative


def number(value: object) -> float:
    result = nonnegative(value)
    if result is None:
        raise ValueError("Expected finite nonnegative number")
    return result


def text(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 1000:
        raise ValueError("Expected bounded nonempty string")
    return value
