from math import radians, cos, sin, sqrt, atan2

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select

from src.api.organizations.models import Organization
from src.api.organizations.models import Building
from src.api.organizations.models import Activity


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

        # Pydantic сам соберёт нужную структуру
        return organization, None
    
    async def search_organizations(self, query: str, offset: int = 0, limit: int = 100):
        # Поиск по полю name (LIKE, case-insensitive)
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


class ActivityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_organizations_by_activity_id(self, activity_id: int, offset: int, limit: int):
        # Проверяем, существует ли вид деятельности
        result = await self.session.execute(
            select(Activity).where(Activity.id == activity_id)
        )
        activity = result.scalar_one_or_none()
        if not activity:
            return None, "Activity not found"

        # Получаем организации с пагинацией
        result = await self.session.execute(
            select(Organization)
            .join(Organization.activities)
            .where(Activity.id == activity_id)
            .offset(offset)
            .limit(limit)
        )
        organizations = result.scalars().all()

        return {
            "offset": offset,
            "limit": limit,
            "organizations": organizations
        }, None
    
    async def get_organizations_by_activity_and_descendants(self, activity_id: int, offset: int, limit: int):
        result = await self.session.execute(
            select(Activity).where(Activity.id == activity_id)
        )
        activity = result.scalar_one_or_none()
        if not activity:
            return None, "Activity not found"

        descendant_ids = await self._get_all_descendant_ids(activity_id)
        all_activity_ids = [activity_id] + descendant_ids

        result = await self.session.execute(
            select(Organization, Activity)
            .join(Organization.activities)
            .where(Activity.id.in_(all_activity_ids))
            .offset(offset)
            .limit(limit)
        )
        rows = result.all()

        org_map = {}
        for org, act in rows:
            if org.id not in org_map:
                org_map[org.id] = {
                    "organization": org,
                    "matched_activities": []
                }
            org_map[org.id]["matched_activities"].append(act)

        organizations = list(org_map.values())

        return {
            "offset": offset,
            "limit": limit,
            "organizations": organizations
        }, None

    async def _get_all_descendant_ids(self, parent_id: int) -> list[int]:
        """Рекурсивно собирает все ID потомков (дети, внуки и т.д.)"""
        result = await self.session.execute(
            select(Activity.id).where(Activity.parent_id == parent_id)
        )
        children = result.scalars().all()

        all_ids = list(children)
        for child_id in children:
            sub_ids = await self._get_all_descendant_ids(child_id)
            all_ids.extend(sub_ids)

        return all_ids


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


    def _format_building_with_orgs(self, buildings):
        """Преобразует список Building в список словарей, совместимых с BuildingWithOrgsResponse"""
        result = []
        for b in buildings:
            result.append({
                "building": b,
                "organizations": b.organizations  # ← уже загружены через selectinload
            })
        return result


    def _distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Расстояние в метрах по приближённой формуле"""
        R = 6371000  # метры
        f1 = radians(lat1)
        f2 = radians(lat2)
        delta_f = radians(lat2 - lat1)
        delta_l = radians(lng2 - lng1)

        a = sin(delta_f / 2) ** 2 + cos(f1) * cos(f2) * sin(delta_l / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

