"""Offline local-stack smoke. Persists one named controlled fixture snapshot."""

import argparse
import json
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    options = parser.parse_args()
    base = options.base_url.rstrip("/")

    def call(path: str, body: dict | None = None) -> dict:
        request = Request(
            base + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json", "X-Request-ID": "compose-smoke"},
            method="POST" if body is not None else "GET",
        )
        with urlopen(request, timeout=60) as response:
            assert response.headers["x-request-id"] == "compose-smoke"
            return json.load(response)

    with urlopen(base, timeout=10) as response:
        assert b'<div id="root">' in response.read()
    assert call("/api/health")["status"] == "ok"
    assert call("/api/health/database")["status"] == "ok"
    ingested = call("/api/repositories/ingest", {
        "path": "golden_repository", "name": "pre-v8-compose-smoke",
    })
    repository_id, snapshot_id = ingested["repository"]["id"], ingested["snapshot"]["id"]
    indexed = call(f"/api/repositories/{repository_id}/snapshots/{snapshot_id}/index", {})
    assert indexed["embedded_chunk_count"] > 0
    answer = call("/api/ask", {
        "repository_id": repository_id, "snapshot_id": snapshot_id,
        "question": "How are overdue invoice fees calculated?", "top_k": 5,
    })
    assert answer["status"] == "answered"
    assert answer["citations"]
    assert answer["generation_provider"] == "deterministic"
    print(json.dumps({
        "repository_id": repository_id, "snapshot_id": snapshot_id,
        "chunks": indexed["embedded_chunk_count"], "citations": len(answer["citations"]),
        "provider": "deterministic", "status": "passed",
    }))


if __name__ == "__main__":
    main()
