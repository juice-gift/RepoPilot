import pytest

from workflow import submit_job


@pytest.mark.parametrize("transient", [True, False])
def test_authentication_precedes_invalid_attempt(transient):
    with pytest.raises(PermissionError):
        submit_job("bad", -1, transient)


@pytest.mark.parametrize("transient", [True, False])
def test_authorized_invalid_attempt_always_rejected(transient):
    with pytest.raises(ValueError):
        submit_job("fixture-authorized", -1, transient)


@pytest.mark.parametrize("attempt", [0, 2, 9])
def test_permanent_rejection(attempt):
    assert submit_job("fixture-authorized", attempt, False) == {"status": "rejected"}


@pytest.mark.parametrize("attempt,delay", [(0, 1), (2, 4), (9, 300), (100000, 300)])
def test_transient_success(attempt, delay):
    assert submit_job("fixture-authorized", attempt, True) == {"status": "scheduled", "delay": delay}
