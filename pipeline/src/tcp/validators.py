"""Deterministic sanity checks for raw data. Pure functions, no I/O."""


def validate_bar(o, h, l, c, v) -> str:  # noqa: E741 - OHLC naming
    """Return a quality flag for one daily OHLCV bar: OK | MISSING | SUSPECT."""
    if any(x is None for x in (o, h, l, c)):
        return "MISSING"
    if min(o, h, l, c) <= 0:
        return "SUSPECT"
    if h < l:
        return "SUSPECT"
    tol = 1e-4
    for x in (o, c):
        if x > h * (1 + tol) or x < l * (1 - tol):
            return "SUSPECT"
    if v is not None and v < 0:
        return "SUSPECT"
    return "OK"
