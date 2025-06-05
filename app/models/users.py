from sqlalchemy import Column, Integer, String, DateTime
from app.db.database import Base
from datetime import datetime, timezone

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True) #index and auto_increment true by default
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)) #lambda will cause to run on every new row
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
