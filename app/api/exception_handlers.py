import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    PersistenceError,
    RefreshTokenReuseError,
    ResourceConflictError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)

ERROR_STATUS_CODES: dict[type[ApplicationError], int] = {
    ResourceNotFoundError: status.HTTP_404_NOT_FOUND,
    ResourceConflictError: status.HTTP_409_CONFLICT,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    RefreshTokenReuseError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    PersistenceError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


async def application_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, ApplicationError):
        raise TypeError("application_exception_handler requires ApplicationError")

    status_code = ERROR_STATUS_CODES.get(type(exc), status.HTTP_400_BAD_REQUEST)
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, AuthenticationError) else None
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled application error",
        extra={"method": request.method, "path": request.url.path},
        exc_info=exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred",
            }
        },
    )
