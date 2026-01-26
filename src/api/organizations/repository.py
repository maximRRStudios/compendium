from math import radians, cos, sin, sqrt, atan2

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select

from src.models import Organization
from src.models import Building
from src.models import Activity


class OrganizationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_building_id(self, building_id: int, offset: int, limit: int):
        # Проверяем, существует ли здание
        building_result = await self.session.execute(
            select(Building).where(Building.id == building_id)
        )
        building = building_result.scalar_one_or_none()
        if not building:
            return None, "Building not found"

        # Получаем организации с предзагрузкой связанных данных
        result = await self.session.execute(
            select(Organization)
            .where(Organization.building_id == building_id)
            .offset(offset)
            .limit(limit)
        )

        organizations = result.scalars().all()

        return {
            "offset": offset,
            "limit": limit,
            "organizations": organizations
        }, None
    
    async def get_organization_by_id(self, org_id: int):
        # Загружаем организацию с нужными связями
        result = await self.session.execute(
            select(Organization)
            .options(
                joinedload(Organization.building),
                selectinload(Organization.phones),
                selectinload(Organization.activities)
                .selectinload(Activity.children)
                .selectinload(Activity.children)
                .selectinload(Activity.children)  # ← 3 уровня
            )
            .where(Organization.id == org_id)
        )
        organization = result.unique().scalar_one_or_none()

        if not organization:
            return None, "Organization not found"

        return organization, None
    
    async def search_organizations(self, query: str, offset: int = 0, limit: int = 100):
        search_pattern = f"%{query.lower()}%"

        # Получение организаций с пагинацией
        result = await self.session.execute(
            select(Organization)
            .where(func.lower(Organization.name).like(search_pattern))
            .offset(offset)
            .limit(limit)
        )
        organizations = result.scalars().all()

        return {
            "offset": offset,
            "limit": limit,
            "organizations": organizations
        }, None
