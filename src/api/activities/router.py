from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.organizations.service import ActivityService
from src.api.schemas import OrganizationResponsePaginated
from src.api.schemas import PaginatedOrgsWithActivitiesResponse
from src.db.session import async_session_general

router_activities = APIRouter(prefix="/activities", tags=["Виды деятельности"])


async def get_db():
    async with async_session_general() as session:
        yield session


@router_activities.get(
    "/{activity_id}/organizations",
    response_model=OrganizationResponsePaginated,
    summary="Возвращает список организаций по виду деятельности"
)
async def get_organizations_by_activity(
    activity_id: int,
    offset: int = Query(0, ge=0, description="Сдвиг записей (для пагинации)"),
    limit: int = Query(100, ge=1, le=1000, description="Макс. количество записей (до 1000)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Поиск организаций по идентификатору вида деятельности(без учета "поддеятельностей").

    - **activity_id**: идентификатор вида деятельности
    """
    service = ActivityService(db)
    result, error = await service.get_organizations_by_activity_id(activity_id, offset=offset, limit=limit)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return result


@router_activities.get(
    "/root/{activity_id}/organizations",
    response_model=PaginatedOrgsWithActivitiesResponse,
    summary="Возвращает список организаций по виду деятельности"
)
async def get_organizations_by_activity_and_children(
    activity_id: int,
    offset: int = Query(0, ge=0, description="Сдвиг записей (для пагинации)"),
    limit: int = Query(100, ge=1, le=1000, description="Макс. количество записей (до 1000)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Поиск организаций по идентификатору вида деятельности и его потомков.

    - **activity_id**: идентификатор вида деятельности
    """
    service = ActivityService(db)
    result, error = await service.get_organizations_by_activity_and_descendants(
        activity_id=activity_id,
        offset=offset,
        limit=limit
    )
    if error:
        raise HTTPException(status_code=404, detail=error)
    return result
