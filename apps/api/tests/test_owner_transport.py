from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from repopilot.api.routes.github import owner_control


@pytest.mark.parametrize(
    "client,server,configured,origin,allowed",
    [
        (("127.0.0.1", 123), ("127.0.0.1", 8000), False, "http://localhost:8082", True),
        (None, ("/run/repopilot-api/api.sock", None), True, "http://localhost:8082", True),
        (None, None, False, "http://localhost:8082", False),
        (None, None, True, "http://localhost:8082", False),
        (("172.18.0.5", 123), ("0.0.0.0", 8000), True, "http://localhost:8082", False),
        (None, None, True, "https://untrusted.example", False),
        (
            ("127.0.0.1", 123),
            ("127.0.0.1", 8000),
            False,
            "https://untrusted.example",
            False,
        ),
        (None, ("0.0.0.0", 8000), True, "http://localhost:8082", False),
    ],
)
def test_owner_requires_exact_origin_and_actual_local_transport(
    client, server, configured, origin, allowed
):
    settings = SimpleNamespace(
        frontend_origin="http://localhost:8082",
        local_owner_unix_socket="/run/repopilot-api/api.sock" if configured else None,
    )
    request = Request(
        {
            "type": "http",
            "client": client,
            "server": server,
            "app": SimpleNamespace(state=SimpleNamespace(settings=settings)),
            # Spoofed forwarding headers never change this decision.
            "headers": [
                (b"origin", origin.encode()),
                (b"x-forwarded-for", b"127.0.0.1"),
            ],
        }
    )
    if allowed:
        owner_control(request)
    else:
        with pytest.raises(HTTPException) as error:
            owner_control(request)
        assert error.value.status_code == 403
