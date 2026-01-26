from src.api.organizations.repository import OrganizationRepository

from sqlalchemy.ext.asyncio import AsyncSession


class OrganizationService:
    def __init__(self, session: AsyncSession):
        self.repo = OrganizationRepository(session)

    async def get_organizations_by_building_id(self, building_id: int, offset: int, limit: int):
        return await self.repo.get_by_building_id(building_id, offset, limit)

    async def get_organization_by_id(self, org_id: int):
        return await self.repo.get_organization_by_id(org_id)
    
    async def search_organizations(self, query: str, offset: int = 0, limit: int = 100):
        return await self.repo.search_organizations(query, offset, limit)


class ActivityService:
    def __init__(self, session: AsyncSession):
        self.repo = ActivityRepository(session)

    async def get_organizations_by_activity_id(self, activity_id: int, offset: int = 0, limit: int = 100):
        return await self.repo.get_organizations_by_activity_id(activity_id, offset, limit)
    
    async def get_organizations_by_activity_and_descendants(self, activity_id: int, offset: int = 0, limit: int = 100):
        return await self.repo.get_organizations_by_activity_and_descendants(activity_id, offset, limit)
