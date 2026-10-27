import pytest

from fees import late_fee


@pytest.mark.parametrize("days,expected", [(0, 0), (1, 100), (2, 200), (30, 3000), (99, 3000)])
def test_overdue_days(days, expected):
    assert late_fee(10000, days) == expected


@pytest.mark.parametrize("balance,days", [(-1, 0), (100, -1)])
def test_invalid_input(balance, days):
    with pytest.raises(ValueError):
        late_fee(balance, days)


def test_integer_rounding_and_zero_balance():
    assert late_fee(1234, 3) == 37
    assert late_fee(0, 5) == 0
