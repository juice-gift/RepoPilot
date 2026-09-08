import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://repopilot:change-me@localhost:5432/repopilot_test",
)
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")
