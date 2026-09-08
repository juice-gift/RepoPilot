from sqlalchemy import text
from sqlalchemy.orm import Session


def check_database_connection(session: Session) -> None:
    result = session.execute(text("SELECT 1"))
    if result.scalar_one() != 1:
        raise RuntimeError("Database connectivity check returned an unexpected result")
