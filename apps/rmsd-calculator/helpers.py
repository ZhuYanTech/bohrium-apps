def option(value, allowed):
    if value not in allowed:
        raise ValueError(f"Expected one of {', '.join(sorted(allowed))}; got {value!r}.")
    return value
