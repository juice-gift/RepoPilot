"""Invoice charges in integer cents; each overdue day is charged, capped at 30 days."""


def late_fee(balance_cents: int, overdue_days: int) -> int:
    if balance_cents < 0 or overdue_days < 0:
        raise ValueError("Values must be nonnegative")
    return balance_cents * min(max(overdue_days - 1, 0), 30) // 100
