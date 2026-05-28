"""
Database adaptado para Vercel usando SQLite async (aiosqlite).
O /tmp é o único diretório gravável no ambiente serverless do Vercel.
"""

import os
import tempfile
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine


class Base(DeclarativeBase):
    pass


# Detecta o diretório temporário correto para cada SO
# No Vercel: /tmp
# No Windows: %TEMP%
# No Linux/Mac: /tmp
if os.name == "nt":
    DB_PATH = Path(tempfile.gettempdir()) / "motordebusca.db"
    DB_PATH_ASYNC = Path(tempfile.gettempdir()) / "motordebusca.db"
else:
    DB_PATH = Path("/tmp") / "motordebusca.db"
    DB_PATH_ASYNC = Path("/tmp") / "motordebusca.db"

os.makedirs(DB_PATH.parent, exist_ok=True)

# Constrói as URLs do SQLite
# No Windows: sqlite:///C:/Users/.../motordebusca.db
# No Linux/Mac: sqlite:///tmp/motordebusca.db
DATABASE_URL_SYNC = f"sqlite:///{DB_PATH}"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH_ASYNC}"

# Async engine com SQLite
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Sync engine (para operações que precisam de sync)
sync_engine = create_engine(
    DATABASE_URL_SYNC,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False},
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
    # Importa os modelos para registrar no metadata
    from app.models import fonte, conteudo, entidade, log
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
