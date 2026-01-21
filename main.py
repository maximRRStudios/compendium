from fastapi import FastAPI
import uvicorn

from src.api import general_router

app = FastAPI(
    title="Compendium API",
    description="API Справочника организаций",
    version="1.0.0",
    contact={
        "name": "Алпатов М.В.",
        "email": "rider16@yandex.ru",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Организации",
            "description": "Работа с организациями"
        },
        {
            "name": "Виды деятельности",
            "description": "Иерархия видов деятельности."
        },
        {
            "name": "Здания",
            "description": "Работа со зданиями."
        }
    ],
    docs_url="/docs"
)
app.include_router(general_router)
