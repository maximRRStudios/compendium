from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.api.organizations.service import OrganizationService
from src.api.buildings.service import BuildingService
from src.api.schemas import OrganizationResponsePaginated
from src.api.schemas import BuildingWithOrgsResponse
from src.db.session import async_session_general


router_buildings = APIRouter(prefix="/buildings", tags=["Здания"])


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
