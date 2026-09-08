import os
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

if not (REPOSITORY_ROOT / ".env").exists():
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://repopilot:change-me@127.0.0.1:5432/repopilot"
        "?connect_timeout=3",
    )
    os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")
