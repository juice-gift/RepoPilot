from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from repopilot.db.health import check_database_connection
from repopilot.db.session import (
    create_database_engine,
    create_database_session_factory,
)


def test_database_engine_and_session_factory_use_configured_url() -> None:
    database_url = "postgresql+psycopg://user:password@localhost:5432/database"
    engine = create_database_engine(database_url)
    session_factory = create_database_session_factory(engine)

    try:
        assert engine.url.render_as_string(hide_password=False) == database_url
        assert session_factory.kw["bind"] is engine
        assert session_factory.kw["expire_on_commit"] is False
    finally:
        engine.dispose()


def test_database_connection_executes_select_one() -> None:
    session = MagicMock(spec=Session)
    session.execute.return_value.scalar_one.return_value = 1

    check_database_connection(session)

    statement = session.execute.call_args.args[0]
    assert str(statement) == "SELECT 1"


def test_database_connection_rejects_unexpected_result() -> None:
    session = MagicMock(spec=Session)
    session.execute.return_value.scalar_one.return_value = 0

    with pytest.raises(RuntimeError, match="unexpected result"):
        check_database_connection(session)
