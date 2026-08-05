from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.exception_handlers import (
    CRUDException,
    crud_exception_handler,
    global_exception_handler,
)
from app.api.router import router
from app.core.config import config

app = FastAPI(
    title=config.project_name,
    version=config.version,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origin_strings,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(CRUDException, crud_exception_handler)

# Include routers
app.include_router(router)

# Mount static folder for serving
app.mount("/public", StaticFiles(directory="public"), name="public")
