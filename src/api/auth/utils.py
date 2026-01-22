from fastapi import Header, HTTPException, Depends
from config import API_KEY
from fastapi.security import APIKeyHeader


api_key_header = APIKeyHeader(name="X-API-Key",
                              auto_error=True,
                              description="Статический API-ключ для доступа ко всем эндпоинтам",
                              scheme_name="API Key")


async def verify_api_key(x_api_key: str = Depends(api_key_header)):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API Key"
        )
    return x_api_key
