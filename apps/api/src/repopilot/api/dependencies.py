from collections.abc import Iterator
from typing import cast

from fastapi import Request
from sqlalchemy.orm import Session

from repopilot.db.session import SessionFactory


def get_database_session(request: Request) -> Iterator[Session]:
    session_factory = cast(
        SessionFactory,
        request.app.state.database_session_factory,
    )
    with session_factory() as session:
        yield session
