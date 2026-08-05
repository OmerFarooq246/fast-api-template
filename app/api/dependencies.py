from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.database import get_db


def get_app_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


SettingsDep = Annotated[Settings, Depends(get_app_settings)]

# Function scope guarantees transaction finalization happens before the response is sent.
SessionDep = Annotated[AsyncSession, Depends(get_db, scope="function")]
