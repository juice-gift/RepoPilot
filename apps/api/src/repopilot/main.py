from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine

from repopilot.api.routes.chunks import router as chunks_router
from repopilot.api.routes.database_health import router as database_health_router
from repopilot.api.routes.health import router as health_router
from repopilot.api.routes.repositories import router as repositories_router
from repopilot.config import Settings
from repopilot.db.session import (
    create_database_engine,
    create_database_session_factory,
)


def create_app(
    settings: Settings | None = None,
    database_engine: Engine | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings()
    resolved_engine = database_engine or create_database_engine(
        resolved_settings.database_url
    )
    session_factory = create_database_session_factory(resolved_engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.database_session_factory = session_factory
        try:
            yield
        finally:
            resolved_engine.dispose()

    app = FastAPI(title="RepoPilot API", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[resolved_settings.frontend_origin],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(database_health_router)
    app.include_router(repositories_router)
    app.include_router(chunks_router)
    return app


app = create_app()
