import io
import json
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from repopilot.diagnostics import JsonFormatter, RequestDiagnostics, logger, request_id


def test_request_metadata_is_correlated_and_does_not_include_sensitive_input():
    app = FastAPI()
    app.add_middleware(RequestDiagnostics)

    @app.get("/items/{item_id}")
    def item(item_id: str):
        return {"id": request_id.get()}

    @app.get("/failure")
    def failure():
        raise RuntimeError("private credential must not be logged")

    output = io.StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    previous = logger.level
    logger.setLevel(logging.INFO)
    try:
        with TestClient(app) as client:
            response = client.get(
                "/items/secret-source?token=private",
                headers={"X-Request-ID": "test-123", "Authorization": "Bearer private"},
            )
            assert response.json() == {"id": "test-123"}
            assert response.headers["x-request-id"] == "test-123"
            failed = client.get("/failure", headers={"X-Request-ID": "invalid id"})
            assert failed.status_code == 500
            assert failed.json() == {"detail": "Internal server error"}
            assert len(failed.headers["x-request-id"]) == 32
        lines = [json.loads(line) for line in output.getvalue().splitlines()]
        assert lines[0]["route"] == "/items/{item_id}"
        assert lines[0]["request_id"] == "test-123"
        assert lines[1]["failure"] == "server_error"
        assert "private" not in output.getvalue()
        assert "secret-source" not in output.getvalue()
        assert request_id.get() is None
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous)
