def retry_delay(attempt: int, transient: bool) -> int | None:
    if attempt < 0:
        raise ValueError("Attempt must be nonnegative")
    if not transient:
        return None
    return min(2 ** attempt, 300)
