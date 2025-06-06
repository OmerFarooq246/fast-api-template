from fastapi import Request
from fastapi.responses import JSONResponse

async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "message": f"An unexpected error occurred: {str(exc)}",
            "success": False,
        },
    )

class CRUDException(Exception):
    def __init__(self, name: str, detail: str, status_code: int = 400):
        self.name = name
        self.detail = detail
        self.status_code = status_code

async def crud_exception_handler(request: Request, exc: CRUDException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": f"CRUD operation error for {exc.name}: {exc.detail}",
            "success": False,
        },
    )