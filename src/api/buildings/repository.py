from math import radians, cos, sin, sqrt, atan2

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select

from src.models import Organization
from src.models import Building


class BuildingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_buildings_in_bbox(self, lat_min: float, lng_min: float, lat_max: float, lng_max: float):
        result = await self.session.execute(
            select(Building)
            .join(Organization)
            .where(
                and_(
                    Building.latitude >= lat_min,
                    Building.latitude <= lat_max,
                    Building.longitude >= lng_min,
                    Building.longitude <= lng_max,
                    )
            )
            .distinct()  # одно здание может иметь несколько орг — убираем дубли
        )
        buildings = result.scalars().all()

        return self._format_building_with_orgs(buildings), None

    async def get_buildings_in_radius(self, lat: float, lng: float, radius: float):
        # Приблизительный фильтр: сначала ограничим область по градусам
        # 1° ≈ 111 км → приблизим радиус
        lat_delta = radius / 111_000
        lng_delta = radius / (111_000 * abs(cos(radians(lat))))

        # Сначала грубый фильтр по прямоугольнику
        result = await self.session.execute(
            select(Building)
            .join(Organization)
            .where(
                and_(
                    Building.latitude >= lat - lat_delta,
                    Building.latitude <= lat + lat_delta,
                    Building.longitude >= lng - lng_delta,
                    Building.longitude <= lng + lng_delta,
                    )
            )
            .distinct()
        )
        buildings = result.scalars().all()

        # Теперь точный фильтр по расстоянию
        filtered_buildings = []
        for b in buildings:
            # Простая формула "haversine" на Python
            if self._distance(lat, lng, b.latitude, b.longitude) <= radius:
                filtered_buildings.append(b)

        # Загружаем организации
        if filtered_buildings:
            result = await self.session.execute(
                select(Building)
                .options(selectinload(Building.organizations))
                .where(Building.id.in_([b.id for b in filtered_buildings]))
            )
            filtered_buildings = result.unique().scalars().all()

        return self._format_building_with_orgs(filtered_buildings), None

    @staticmethod
    def _format_building_with_orgs(buildings):
        """Преобразует список Building в список словарей, совместимых с BuildingWithOrgsResponse"""
        result = []
        for b in buildings:
            result.append({
                "building": b,
                "organizations": b.organizations  # ← уже загружены через selectinload
            })
        return result

    @staticmethod
    def _distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Расстояние в метрах по приближённой формуле"""
        r = 6371000  # метры
        f1 = radians(lat1)
        f2 = radians(lat2)
        delta_f = radians(lat2 - lat1)
        delta_l = radians(lng2 - lng1)

        a = sin(delta_f / 2) ** 2 + cos(f1) * cos(f2) * sin(delta_l / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return r * c
