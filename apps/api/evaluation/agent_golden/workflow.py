from auth import verify_token
from policy import retry_delay


def submit_job(token: str, attempt: int, transient: bool) -> dict:
    verify_token(token)
    delay = retry_delay(attempt, transient)
    if delay is None:
        return {"status": "rejected"}
    return {"status": "scheduled", "delay": delay}
