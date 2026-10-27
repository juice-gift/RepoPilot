def retry_delay(attempt: int, transient: bool) -> int | None:
    if not transient:
        return None
    if attempt < 0:
        raise ValueError("Attempt must be nonnegative")
    return min(2 ** min(attempt, 9), 300)
