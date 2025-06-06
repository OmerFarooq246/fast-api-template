from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import config
from app.api.router import router
from app.api.exception_handlers import global_exception_handler, CRUDException, crud_exception_handler

app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.VERSION,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ORIGINS,
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
app.mount("/public", StaticFiles(directory="app/public"), name="public")