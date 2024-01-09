from sqlalchemy.ext.asyncio import (AsyncAttrs, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    pass


engine = create_async_engine(
    'postgresql+asyncpg://postgres:postgres@localhost/accounts')
async_session = async_sessionmaker(engine, expire_on_commit=False)
