from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.api.organizations.service import OrganizationService
from src.api.organizations.service import ActivityService
from src.api.organizations.service import BuildingService


from src.api.organizations.schemas import OrganizationResponsePaginated
from src.api.organizations.schemas import BuildingWithOrgsResponse
from src.api.organizations.schemas import OrganizationFullResponse
from src.api.organizations.schemas import PaginatedOrgsWithActivitiesResponse
from src.db.session import async_session_general



router_buildings = APIRouter(prefix="/buildings", tags=["Здания"])
router_activities = APIRouter(prefix="/activities", tags=["Виды деятельности"])
router_organizations = APIRouter(prefix="/organizations", tags=["Организации"])

async def get_db():
    async with async_session_general() as session:
        yield session


@router_buildings.get(
    "/{building_id}/organizations",
    response_model=OrganizationResponsePaginated,
    summary="Возвращает список организаций в здании"
)
async def get_organizations_in_building(
    building_id: int,
    offset: int = Query(0, ge=0, description="Сдвиг записей (для пагинации)"),
    limit: int = Query(100, ge=1, le=1000, description="Макс. количество записей (до 1000)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает список организаций в здании

    - **building_id**: Идентификатор здания

    """
    service = OrganizationService(db)
    organizations, error = await service.get_organizations_by_building_id(building_id, offset=offset, limit=limit)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return organizations


@router_buildings.get(
    "/organizations/nearby",
    response_model=list[BuildingWithOrgsResponse],
    summary="Возвращает список зданий и организаций по координатам на карте"
)
async def get_buildings_nearby(
    # Для box
    lat_min: Optional[float] = Query(None, ge=-90, le=90, description="минимальная широта (южная граница)"),
    lng_min: Optional[float] = Query(None, ge=-180, le=180, description="минимальная долгота (западная граница)"),
    lat_max: Optional[float] = Query(None, ge=-90, le=90, description="максимальная широта (северная граница)"),
    lng_max: Optional[float] = Query(None, ge=-180, le=180, description="максимальная долгота (восточная граница)"),
    # Для радиуса
    lat: Optional[float] = Query(None, ge=-90, le=90, description="широта центра (для поиска по радиусу)"),
    lng: Optional[float] = Query(None, ge=-180, le=180, description="долгота центра"),
    radius: Optional[float] = Query(None, gt=0, le=50_000, description="радиус поиска в метрах"),
    db: AsyncSession = Depends(get_db),
):
    """
    список организаций, которые находятся в заданном радиусе/прямоугольной области
    относительно указанной точки на карте. список зданий
    Если переданы все параметры, используется поиск по прямоугольнику

    - **lat_min**: минимальная широта (южная граница)
    - **lng_min**: минимальная долгота (западная граница)
    - **lat_max**: максимальная широта (северная граница)
    - **lng_max**: максимальная долгота (восточная граница)
    - **lat**: широта центра (для поиска по радиусу)
    - **lng**: долгота центра
    - **radius**: радиус поиска в метрах
    """
    service = BuildingService(db)

    # Проверяем, какой режим
    if lat_min is not None and lng_min is not None and lat_max is not None and lng_max is not None:
        result, error = await service.get_buildings_in_bbox(lat_min, lng_min, lat_max, lng_max)
    elif lat is not None and lng is not None and radius is not None:
        result, error = await service.get_buildings_in_radius(lat, lng, radius)
    else:
        raise HTTPException(
            status_code=400,
            detail="Either (lat_min, lng_min, lat_max, lng_max) or (lat, lng, radius) must be provided"
        )

    if error:
        raise HTTPException(status_code=404, detail=error)

    return result


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


@router_organizations.get(
    "/search",
    response_model=OrganizationResponsePaginated,
    summary="Поиск организаций по названию"
)
async def search_organizations(
    query: str = Query(min_length=1, description="Поисковый запрос (по названию)"),
    offset: int = Query(0, ge=0, description="Сдвиг записей (для пагинации)"),
    limit: int = Query(100, ge=1, le=1000, description="Макс. количество записей (до 1000)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Поиск организаций по названию (частичное совпадение, без учёта регистра(для латиницы, по кириллице привет SQLite))

    - **query**: подстрока для поиска
    """
    service = OrganizationService(db)
    result, error = await service.search_organizations(query, offset=offset, limit=limit)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return result


@router_organizations.get(
    "/{org_id}",
    response_model=OrganizationFullResponse,
    summary="Поиск организаций по идентификатору"
)
async def get_organization_by_id(
    org_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить полную информацию об организации.

    - **org_id**: идентификатор организации
    - Возвращает: название, здание, телефоны, виды деятельности (до 3 уровней)
    """
    service = OrganizationService(db)
    org, error = await service.get_organization_by_id(org_id)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return org

