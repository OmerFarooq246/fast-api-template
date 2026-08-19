from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import final
from uuid import UUID, uuid4

from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AuthenticationError
from app.core.security import (
    TokenClaims,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.models.users import User
from app.repositories.refresh_session_repository import (
    RefreshSessionRepository,
    refresh_session_repository,
)
from app.services.user_service import UserService, user_service


@dataclass(frozen=True, slots=True)
@final
class TokenPairData:
    access_token: str
    refresh_token: str
    user: User


@dataclass(frozen=True, slots=True)
@final
class RefreshReuseDetected:
    """Signals that the token family was revoked and the transaction should commit."""


def digest_jti(jti: str) -> str:
    return sha256(jti.encode()).hexdigest()


class AuthService:
    def __init__(
        self,
        users: UserService,
        refresh_sessions: RefreshSessionRepository,
    ) -> None:
        self.users = users
        self.refresh_sessions = refresh_sessions

    async def login(
        self,
        session: AsyncSession,
        *,
        email: str,
        password: str,
        settings: Settings,
    ) -> TokenPairData:
        user = await self.users.authenticate(session, email, password)
        return await self._issue_token_pair(session, user=user, settings=settings)

    async def rotate(
        self,
        session: AsyncSession,
        *,
        refresh_token: str,
        settings: Settings,
    ) -> TokenPairData | RefreshReuseDetected:
        claims = self._decode_refresh_token(refresh_token, settings)
        user_id = self._parse_subject(claims.sub)
        stored_session = await self.refresh_sessions.get_for_update(session, digest_jti(claims.jti))
        if stored_session is None:
            raise AuthenticationError("Invalid or expired refresh token")
        if stored_session.revoked_at is not None:
            await self.refresh_sessions.revoke_family(session, stored_session.family_id)
            return RefreshReuseDetected()
        if stored_session.user_id != user_id:
            await self.refresh_sessions.revoke_family(session, stored_session.family_id)
            return RefreshReuseDetected()

        user = await self.users.get_authenticated_user(session, user_id)
        await self.refresh_sessions.revoke(session, stored_session)
        return await self._issue_token_pair(
            session,
            user=user,
            settings=settings,
            family_id=stored_session.family_id,
        )

    async def logout(
        self,
        session: AsyncSession,
        *,
        refresh_token: str,
        settings: Settings,
    ) -> None:
        claims = self._decode_refresh_token(refresh_token, settings)
        stored_session = await self.refresh_sessions.get_for_update(session, digest_jti(claims.jti))
        if stored_session is not None and stored_session.revoked_at is None:
            await self.refresh_sessions.revoke(session, stored_session)

    async def change_password(
        self,
        session: AsyncSession,
        *,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        await self.users.change_password(
            session,
            user,
            current_password=current_password,
            new_password=new_password,
        )
        await self.refresh_sessions.revoke_all_for_user(session, user.id)

    async def logout_all(self, session: AsyncSession, *, user: User) -> None:
        await self.refresh_sessions.revoke_all_for_user(session, user.id)

    async def _issue_token_pair(
        self,
        session: AsyncSession,
        *,
        user: User,
        settings: Settings,
        family_id: UUID | None = None,
    ) -> TokenPairData:
        jti = str(uuid4())
        refresh_lifetime = timedelta(days=settings.refresh_token_expire_days)
        await self.refresh_sessions.create(
            session,
            user_id=user.id,
            jti_digest=digest_jti(jti),
            family_id=family_id or uuid4(),
            expires_at=datetime.now(UTC) + refresh_lifetime,
        )
        return TokenPairData(
            access_token=create_access_token(user.id, settings=settings),
            refresh_token=create_refresh_token(
                user.id,
                settings=settings,
                expires_delta=refresh_lifetime,
                jti=jti,
            ),
            user=user,
        )

    @staticmethod
    def _decode_refresh_token(refresh_token: str, settings: Settings) -> TokenClaims:
        try:
            return decode_refresh_token(refresh_token, settings)
        except InvalidTokenError as exc:
            raise AuthenticationError("Invalid or expired refresh token") from exc

    @staticmethod
    def _parse_subject(subject: str) -> int:
        try:
            return int(subject)
        except ValueError as exc:
            raise AuthenticationError("Invalid or expired refresh token") from exc


auth_service = AuthService(user_service, refresh_session_repository)
