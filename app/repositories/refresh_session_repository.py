from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_sessions import RefreshSession


class RefreshSessionRepository:
    async def create(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        jti_digest: str,
        family_id: UUID,
        expires_at: datetime,
    ) -> RefreshSession:
        refresh_session = RefreshSession(
            user_id=user_id,
            jti_digest=jti_digest,
            family_id=family_id,
            expires_at=expires_at,
        )
        session.add(refresh_session)
        await session.flush()
        return refresh_session

    async def get_for_update(self, session: AsyncSession, jti_digest: str) -> RefreshSession | None:
        result = await session.execute(
            select(RefreshSession).where(RefreshSession.jti_digest == jti_digest).with_for_update()
        )
        return result.scalar_one_or_none()

    async def revoke(self, session: AsyncSession, refresh_session: RefreshSession) -> None:
        refresh_session.revoked_at = datetime.now(UTC)
        await session.flush()

    async def revoke_family(self, session: AsyncSession, family_id: UUID) -> None:
        await session.execute(
            update(RefreshSession)
            .where(
                RefreshSession.family_id == family_id,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await session.flush()

    async def revoke_all_for_user(self, session: AsyncSession, user_id: int) -> None:
        await session.execute(
            update(RefreshSession)
            .where(
                RefreshSession.user_id == user_id,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await session.flush()


refresh_session_repository = RefreshSessionRepository()
