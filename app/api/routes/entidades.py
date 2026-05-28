from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models import Entidade, TipoEntidade, ConteudoEntidade
from app.schemas.stats import EntidadeFrequencia

router = APIRouter(prefix="/entidades", tags=["Entidades"])


@router.get("", response_model=list[EntidadeFrequencia])
async def listar_entidades(
    tipo: Optional[str] = None,
    busca: Optional[str] = None,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    query = select(Entidade).order_by(Entidade.frequencia.desc())

    if tipo:
        query = query.where(Entidade.tipo == tipo)
    if busca:
        query = query.where(Entidade.nome.ilike(f"%{busca}%"))

    query = query.offset((pagina - 1) * por_pagina).limit(por_pagina)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/tipos")
async def listar_tipos(db: AsyncSession = Depends(get_db)):
    """Retorna tipos de entidades com contagem."""
    result = await db.execute(
        select(Entidade.tipo, func.count(Entidade.id).label("total"))
        .group_by(Entidade.tipo)
        .order_by(func.count(Entidade.id).desc())
    )
    return [{"tipo": row[0], "total": row[1]} for row in result.fetchall()]


@router.get("/top/{tipo}")
async def top_entidades(
    tipo: str,
    limite: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Retorna as entidades mais frequentes de um tipo."""
    result = await db.execute(
        select(Entidade)
        .where(Entidade.tipo == tipo)
        .order_by(Entidade.frequencia.desc())
        .limit(limite)
    )
    return result.scalars().all()
