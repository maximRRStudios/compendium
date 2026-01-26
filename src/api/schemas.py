from typing import List
from pydantic import BaseModel


class Building(BaseModel):
    address: str
    latitude: float
    longitude: float

    class Config:
        from_attributes = True


class BuildingResponse(Building):
    id: int

    class Config:
        from_attributes = True


# Схемы для Activity
class Activity(BaseModel):
    name: str
    parent_id: int | None = None


class ActivityResponseFull(Activity):
    id: int
    children: list["ActivityResponseFull"] = []

    class Config:
        from_attributes = True


# Обратная ссылка для предотвращения RecursionError
ActivityResponseFull.model_rebuild()


# Схемы для Phone
class Phone(BaseModel):
    number: str


class PhoneResponse(Phone):
    id: int

    class Config:
        from_attributes = True


# Схемы для Organization
class Organization(BaseModel):
    id: int
    name: str


class OrganizationResponsePaginated(BaseModel):
    offset: int
    limit: int
    organizations: List[Organization]

    class Config:
        from_attributes = True


class OrganizationResponse(Organization):
    id: int

    class Config:
        from_attributes = True


class BuildingWithOrgsResponse(BaseModel):
    building: BuildingResponse
    organizations: List[Organization]

    class Config:
        from_attributes = True


class OrganizationFullResponse(BaseModel):
    id: int
    name: str
    building: BuildingResponse
    phones: List[PhoneResponse]
    activities: List[ActivityResponseFull]

    class Config:
        from_attributes = True


class ActivityResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class OrganizationWithActivitiesResponse(BaseModel):
    organization: OrganizationResponse
    matched_activities: List[ActivityResponse]

    class Config:
        from_attributes = True


class PaginatedOrgsWithActivitiesResponse(BaseModel):
    offset: int
    limit: int
    organizations: List[OrganizationWithActivitiesResponse]

    class Config:
        from_attributes = True
