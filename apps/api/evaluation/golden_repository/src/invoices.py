"""Invoice calculations for the Golden Repository."""

from decimal import Decimal


def calculate_late_fee(balance: Decimal, days_overdue: int) -> Decimal:
    """Charge one percent per overdue week, capped at ten percent."""
    overdue_weeks = max(days_overdue, 0) // 7
    rate = min(Decimal("0.01") * overdue_weeks, Decimal("0.10"))
    return (balance * rate).quantize(Decimal("0.01"))


def format_invoice_number(sequence: int) -> str:
    """Render the public invoice identifier."""
    return f"INV-{sequence:08d}"
