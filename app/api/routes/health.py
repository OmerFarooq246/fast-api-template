import asyncio
import logging
from typing import cast

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.dependencies import SettingsDep
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/live", response_model=HealthResponse, summary="Check process liveness")
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
    summary="Check service readiness",
)
async def readiness(request: Request, settings: SettingsDep) -> HealthResponse | JSONResponse:
    engine = cast(AsyncEngine, request.app.state.db_engine)
    try:
        async with asyncio.timeout(settings.readiness_timeout_seconds):
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
    except (TimeoutError, SQLAlchemyError):
        logger.exception("Readiness check failed")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=HealthResponse(status="unavailable").model_dump(),
        )
    return HealthResponse(status="ok")
