from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.organizations.service import OrganizationService
from src.api.schemas import OrganizationResponsePaginated
from src.api.schemas import OrganizationFullResponse
from src.db.session import async_session_general


router_organizations = APIRouter(prefix="/organizations", tags=["Организации"])

async def get_db():
    async with async_session_general() as session:
        yield session






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
