import pytest
from pydantic import ValidationError

from app.models.users import UserRole
from app.schemas.users import UserAdminUpdate, UserCreate, UserPage


def test_user_email_is_normalized() -> None:
    user = UserCreate(
        email="Person@EXAMPLE.COM",
        password="long-enough-password",  # noqa: S106
    )

    assert user.email == "person@example.com"


def test_public_registration_cannot_assign_a_role() -> None:
    with pytest.raises(ValidationError):
        UserCreate.model_validate(
            {
                "email": "person@example.com",
                "password": "long-enough-password",
                "role": UserRole.SUPER_ADMIN,
            }
        )


def test_admin_update_cannot_write_a_password() -> None:
    with pytest.raises(ValidationError):
        UserAdminUpdate.model_validate({"password": "plaintext-password"})


def test_invalid_roles_are_rejected() -> None:
    with pytest.raises(ValidationError):
        UserAdminUpdate(role="OWNER")


def test_empty_user_page_is_a_valid_response() -> None:
    page = UserPage(items=[], page=1, size=20, total=0, pages=0)

    assert page.items == []
