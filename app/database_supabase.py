"""
Database adaptado para Supabase (PostgreSQL).
Funciona tanto no Vercel quanto localmente.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from app.config_vercel import settings


class Base(DeclarativeBase):
    pass


# Usa as URLs do ambiente (Supabase ou SQLite fallback)
DATABASE_URL = os.environ.get("DATABASE_URL", settings.database_url)
DATABASE_URL_SYNC = os.environ.get("DATABASE_URL_SYNC", settings.database_url_sync)

# Se for PostgreSQL, ajusta o driver
if DATABASE_URL.startswith("postgresql://"):
    # Sync URL já está correta
    pass
elif DATABASE_URL.startswith("postgres://"):
    # Alguns serviços usam postgres:// em vez de postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    DATABASE_URL_SYNC = DATABASE_URL_SYNC.replace("postgres://", "postgresql://", 1)

# Async URL precisa do driver asyncpg
if "postgresql://" in DATABASE_URL and "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Cria os engines
engine_kwargs = {}
if "sqlite" in DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    **engine_kwargs,
)

sync_engine = create_engine(
    DATABASE_URL_SYNC,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Cria as tabelas se não existirem."""
    from app.models import fonte, conteudo, entidade, log
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
