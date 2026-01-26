from src.api.activities.repository import ActivityRepository

from sqlalchemy.ext.asyncio import AsyncSession


class ActivityService:
    def __init__(self, session: AsyncSession):
        self.repo = ActivityRepository(session)

    async def get_organizations_by_activity_id(self, activity_id: int, offset: int = 0, limit: int = 100):
        return await self.repo.get_organizations_by_activity_id(activity_id, offset, limit)

    async def get_organizations_by_activity_and_descendants(self, activity_id: int, offset: int = 0, limit: int = 100):
        return await self.repo.get_organizations_by_activity_and_descendants(activity_id, offset, limit)
