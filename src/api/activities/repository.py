from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models import Organization
from src.models import Activity


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
