from fastapi import APIRouter, Depends

from src.api.auth.utils import verify_api_key
from src.api.buildings.router import router_buildings
from src.api.activities.router import router_activities
from src.api.organizations.router import router_organizations


general_router = APIRouter(dependencies=[Depends(verify_api_key)])

general_router.include_router(router_buildings)
general_router.include_router(router_activities)
general_router.include_router(router_organizations)
