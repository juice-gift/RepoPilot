"""Application configuration for the Golden Repository."""

import os


class MissingDatabaseUrlError(RuntimeError):
    """Raised when the database connection string is absent."""


def require_database_url() -> str:
    """Read DATABASE_URL and reject startup when it is missing."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise MissingDatabaseUrlError("DATABASE_URL must be configured")
    return database_url
