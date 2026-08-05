from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.exception_handlers import (
    CRUDException,
    crud_exception_handler,
    global_exception_handler,
)
from app.api.router import router
from app.core.config import Settings, get_settings
from app.db.database import engine

PUBLIC_DIRECTORY = Path(__file__).resolve().parent.parent / "public"


def create_app(settings: Settings | None = None) -> FastAPI:
    application_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        await engine.dispose()

    application = FastAPI(
        title=application_settings.project_name,
        version=application_settings.version,
        debug=application_settings.debug,
        lifespan=lifespan,
    )
    application.state.settings = application_settings

    application.add_middleware(
        CORSMiddleware,
        allow_origins=application_settings.cors_origin_strings,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.add_exception_handler(Exception, global_exception_handler)
    application.add_exception_handler(CRUDException, crud_exception_handler)
    application.include_router(router)
    application.mount("/public", StaticFiles(directory=PUBLIC_DIRECTORY), name="public")

    return application


app = create_app()
