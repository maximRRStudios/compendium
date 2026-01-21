from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import DATABASE_CONNECTION_STRING

engine_general = create_async_engine(
    DATABASE_CONNECTION_STRING
)

async_session_general = async_sessionmaker(engine_general, expire_on_commit=False)
