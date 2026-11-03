import pytest
import itsdangerous
from itsdangerous import SignatureExpired, TimestampSigner

assert itsdangerous.__file__.startswith("/workspace/src/itsdangerous/")


class ClockSigner(TimestampSigner):
    now = 10000

    def get_timestamp(self):
        return self.now


@pytest.mark.parametrize("max_age", [0, 10, 60])
def test_future_timestamp_is_rejected(max_age):
    signer = ClockSigner("offline-test-key")
    signed = signer.sign(b"payload")
    signer.now = 9999
    with pytest.raises(SignatureExpired):
        signer.unsign(signed, max_age=max_age)


@pytest.mark.parametrize("age,max_age", [(0, 0), (1, 5), (5, 5)])
def test_valid_age_is_accepted(age, max_age):
    signer = ClockSigner("offline-test-key")
    signed = signer.sign(b"payload")
    signer.now += age
    assert signer.unsign(signed, max_age=max_age) == b"payload"


def test_old_timestamp_is_rejected():
    signer = ClockSigner("offline-test-key")
    signed = signer.sign(b"payload")
    signer.now += 11
    with pytest.raises(SignatureExpired):
        signer.unsign(signed, max_age=10)


def test_no_age_limit_preserves_existing_behavior():
    signer = ClockSigner("offline-test-key")
    signed = signer.sign(b"payload")
    signer.now -= 1
    assert signer.unsign(signed) == b"payload"
