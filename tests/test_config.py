import pytest
from pydantic import ValidationError

from app.core.config import DEVELOPMENT_SECRET, Environment, Settings


def test_production_requires_a_strong_secret() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY must be changed"):
        Settings(
            environment=Environment.PRODUCTION,
            secret_key=DEVELOPMENT_SECRET,
        )


def test_database_uri_requires_asyncpg() -> None:
    with pytest.raises(ValidationError, match=r"postgresql\+asyncpg"):
        Settings(database_uri="postgresql://postgres:postgres@localhost/app")
