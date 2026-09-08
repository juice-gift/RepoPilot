import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://repopilot:change-me@127.0.0.1:5432/repopilot_test"
    "?connect_timeout=3",
)
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")
