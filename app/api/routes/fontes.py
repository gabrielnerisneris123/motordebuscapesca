from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional

from app.database import get_db
from app.models import Fonte, FonteStatus
from app.schemas.fonte import FonteCreate, FonteRead, FonteList, FonteUpdate
from app.crawler.discovery import cadastrar_fonte, expandir_fonte, ciclo_descoberta

router = APIRouter(prefix="/fontes", tags=["Fontes"])


@router.get("", response_model=FonteList)
async def listar_fontes(
    status: Optional[str] = None,
    categoria: Optional[str] = None,
    busca: Optional[str] = None,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Fonte).order_by(Fonte.score_relevancia.desc())

    if status:
        query = query.where(Fonte.status == status)
    if categoria:
        query = query.where(Fonte.categoria == categoria)
    if busca:
        query = query.where(
            Fonte.dominio.ilike(f"%{busca}%") | Fonte.nome.ilike(f"%{busca}%")
        )

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.offset((pagina - 1) * por_pagina).limit(por_pagina)
    result = await db.execute(query)
    fontes = result.scalars().all()

    return FonteList(
        items=fontes,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=(total + por_pagina - 1) // por_pagina,
    )


@router.get("/{fonte_id}", response_model=FonteRead)
async def obter_fonte(fonte_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Fonte).where(Fonte.id == fonte_id))
    fonte = result.scalar_one_or_none()
    if not fonte:
        raise HTTPException(status_code=404, detail="Fonte não encontrada")
    return fonte


@router.post("", response_model=FonteRead, status_code=201)
async def criar_fonte(
    dados: FonteCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    fonte = await cadastrar_fonte(dados.url, db, descoberta_via="manual", nome=dados.nome or "")
    if not fonte:
        raise HTTPException(status_code=400, detail="URL inválida ou inacessível")
    await db.commit()
    return fonte


@router.patch("/{fonte_id}", response_model=FonteRead)
async def atualizar_fonte(
    fonte_id: int,
    dados: FonteUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Fonte).where(Fonte.id == fonte_id))
    fonte = result.scalar_one_or_none()
    if not fonte:
        raise HTTPException(status_code=404, detail="Fonte não encontrada")

    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(fonte, campo, valor)

    await db.commit()
    return fonte


@router.delete("/{fonte_id}", status_code=204)
async def deletar_fonte(fonte_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Fonte).where(Fonte.id == fonte_id))
    fonte = result.scalar_one_or_none()
    if not fonte:
        raise HTTPException(status_code=404, detail="Fonte não encontrada")
    await db.delete(fonte)
    await db.commit()


@router.post("/{fonte_id}/expandir")
async def expandir(
    fonte_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Crawla a fonte para descobrir novas URLs."""
    result = await db.execute(select(Fonte).where(Fonte.id == fonte_id))
    fonte = result.scalar_one_or_none()
    if not fonte:
        raise HTTPException(status_code=404, detail="Fonte não encontrada")

    background_tasks.add_task(expandir_fonte, fonte_id, db)
    return {"mensagem": "Expansão iniciada em background"}


@router.post("/descoberta/iniciar")
async def iniciar_descoberta(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Inicia ciclo de descoberta automática de novas fontes."""
    background_tasks.add_task(ciclo_descoberta, db)
    return {"mensagem": "Ciclo de descoberta iniciado"}
