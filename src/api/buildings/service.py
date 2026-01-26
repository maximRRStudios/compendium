from sqlalchemy.ext.asyncio import AsyncSession

from src.api.buildings.repository import BuildingRepository


class BuildingService:
    def __init__(self, session: AsyncSession):
        self.repo = BuildingRepository(session)

    async def get_buildings_in_bbox(self, lat_min: float, lng_min: float, lat_max: float, lng_max: float):
        return await self.repo.get_buildings_in_bbox(lat_min, lng_min, lat_max, lng_max)

    async def get_buildings_in_radius(self, lat: float, lng: float, radius: float):
        return await self.repo.get_buildings_in_radius(lat, lng, radius)
