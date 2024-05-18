# Copyright (c) 2024 Sebastian Pipping <sebastian@pipping.org>
# Licensed under Affero GPL v3 or later


def shortest_first_rotated(values: list[str]) -> list[str]:
    """
    Rotate a cycle of values so that the shortest item goes first.

    >>> shortest_first_rotated(["22", "x", "1", "333"])
    ["1", "333", "22", "x"]
    """
    # Do we even have enough values to rotate?
    if len(values) < 2:  # noqa: PLR2004
        return values

    _1, _2, index = min((len(v), v, i) for i, v in enumerate(values))
    return values[index:] + values[:index]
