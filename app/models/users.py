from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, Enum
from app.db.database import Base
from datetime import datetime, timezone
import enum

class UserRoles(enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    USER = "USER"

class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True) #index and auto_increment true by default
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True) #index=True for faster lookups, via a datastructure maintained by engine
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRoles] = mapped_column(Enum(UserRoles), nullable=False, default=UserRoles.USER)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    ) #lambda will cause to run on every new row
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
