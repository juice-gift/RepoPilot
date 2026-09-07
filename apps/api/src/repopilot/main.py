from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from repopilot.api.routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="RepoPilot API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    return app


app = create_app()
