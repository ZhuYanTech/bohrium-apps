def wrapped(sequence, width):
    if not 0 <= width <= 200:
        raise ValueError("Line width must be from 0 to 200.")
    return "\n".join(sequence[i:i + width] for i in range(0, len(sequence), width)) if width else sequence


def option(value, allowed):
    if value not in allowed:
        raise ValueError(f"Expected one of {', '.join(sorted(allowed))}; got {value!r}.")
    return value
