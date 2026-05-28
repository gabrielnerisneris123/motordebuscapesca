from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from app.database import get_db
from app.models import Conteudo, ConteudoStatus
from app.schemas.conteudo import ConteudoRead, ConteudoDetalhe, ConteudoList
from app.processing.pipeline import processar_conteudo

router = APIRouter(prefix="/conteudos", tags=["Conteúdos"])


@router.get("", response_model=ConteudoList)
async def listar_conteudos(
    fonte_id: Optional[int] = None,
    status: Optional[str] = None,
    busca: Optional[str] = None,
    score_min: Optional[float] = None,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Conteudo).order_by(Conteudo.data_coleta.desc())

    if fonte_id:
        query = query.where(Conteudo.fonte_id == fonte_id)
    if status:
        query = query.where(Conteudo.status == status)
    if busca:
        query = query.where(
            or_(
                Conteudo.titulo.ilike(f"%{busca}%"),
                Conteudo.conteudo_texto.ilike(f"%{busca}%"),
            )
        )
    if score_min is not None:
        query = query.where(Conteudo.score_relevancia >= score_min)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.offset((pagina - 1) * por_pagina).limit(por_pagina)
    result = await db.execute(query)
    conteudos = result.scalars().all()

    return ConteudoList(
        items=conteudos,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=(total + por_pagina - 1) // por_pagina,
    )


@router.get("/{conteudo_id}", response_model=ConteudoDetalhe)
async def obter_conteudo(conteudo_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conteudo).where(Conteudo.id == conteudo_id))
    conteudo = result.scalar_one_or_none()
    if not conteudo:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado")
    return conteudo


@router.post("/{conteudo_id}/processar")
async def processar(conteudo_id: int, db: AsyncSession = Depends(get_db)):
    """Reprocessa um conteúdo específico."""
    result = await db.execute(select(Conteudo).where(Conteudo.id == conteudo_id))
    conteudo = result.scalar_one_or_none()
    if not conteudo:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado")

    sucesso = await processar_conteudo(conteudo_id, db)
    await db.commit()
    return {"sucesso": sucesso}


@router.get("/exportar/csv")
async def exportar_csv(
    fonte_id: Optional[int] = None,
    score_min: float = 1.0,
    db: AsyncSession = Depends(get_db),
):
    """Exporta conteúdos como CSV."""
    import io
    import csv
    from fastapi.responses import StreamingResponse

    query = select(Conteudo).where(
        Conteudo.status == ConteudoStatus.PROCESSADO.value,
        Conteudo.score_relevancia >= score_min,
    ).order_by(Conteudo.data_coleta.desc()).limit(10000)

    if fonte_id:
        query = query.where(Conteudo.fonte_id == fonte_id)

    result = await db.execute(query)
    conteudos = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "url", "titulo", "autor", "data_publicacao", "data_coleta",
                     "num_palavras", "score_relevancia", "tags"])

    for c in conteudos:
        writer.writerow([
            c.id, c.url, c.titulo or "", c.autor or "",
            c.data_publicacao or "", c.data_coleta,
            c.num_palavras, c.score_relevancia,
            "|".join(c.tags or []),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=conteudos.csv"},
    )
