"""
Rotas de controle de coleta: iniciar, pausar, status, agendamento.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.database import get_db
from app.models import Fonte, Conteudo, ConteudoStatus, FonteStatus
from app.crawler.scraper import coletar_lote
from app.crawler.discovery import ciclo_descoberta, descobrir_sitemap, descobrir_rss
from app.processing.pipeline import processar_conteudo

router = APIRouter(prefix="/coleta", tags=["Coleta"])


@router.post("/iniciar/{fonte_id}")
async def iniciar_coleta_fonte(
    fonte_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Inicia coleta para uma fonte específica."""
    result = await db.execute(select(Fonte).where(Fonte.id == fonte_id))
    fonte = result.scalar_one_or_none()
    if not fonte:
        raise HTTPException(status_code=404, detail="Fonte não encontrada")

    background_tasks.add_task(_executar_coleta_fonte, fonte_id)
    return {"mensagem": f"Coleta iniciada para {fonte.dominio}"}


@router.post("/iniciar-todas")
async def iniciar_coleta_todas(
    background_tasks: BackgroundTasks,
    limite_por_fonte: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Inicia coleta para todas as fontes ativas."""
    result = await db.execute(
        select(Fonte).where(Fonte.status == FonteStatus.ATIVA.value)
    )
    fontes = result.scalars().all()

    for fonte in fontes:
        background_tasks.add_task(_executar_coleta_fonte, fonte.id)

    return {"mensagem": f"Coleta iniciada para {len(fontes)} fontes"}


@router.post("/processar-pendentes")
async def processar_pendentes(
    background_tasks: BackgroundTasks,
    limite: int = 500,
    db: AsyncSession = Depends(get_db),
):
    """Processa conteúdos coletados mas não processados."""
    result = await db.execute(
        select(Conteudo.id)
        .where(Conteudo.status == ConteudoStatus.COLETADO.value)
        .limit(limite)
    )
    ids = [r[0] for r in result.fetchall()]

    background_tasks.add_task(_processar_lote_ids, ids)
    return {"mensagem": f"{len(ids)} conteúdos enviados para processamento"}


@router.post("/descobrir-sitemap/{fonte_id}")
async def descobrir_sitemap_fonte(
    fonte_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Descobre e indexa sitemap de uma fonte."""
    result = await db.execute(select(Fonte).where(Fonte.id == fonte_id))
    fonte = result.scalar_one_or_none()
    if not fonte:
        raise HTTPException(status_code=404, detail="Fonte não encontrada")

    urls = await descobrir_sitemap(fonte.url)
    urls_rss = await descobrir_rss(fonte.url)

    novos = 0
    for url in urls + urls_rss:
        result = await db.execute(select(Conteudo).where(Conteudo.url == url))
        if not result.scalar_one_or_none():
            conteudo = Conteudo(
                fonte_id=fonte_id,
                url=url,
                status="pendente",
                data_coleta=datetime.utcnow(),
            )
            db.add(conteudo)
            novos += 1

    if urls:
        fonte.tem_sitemap = True
        fonte.url_sitemap = urls[0] if urls else None
    if urls_rss:
        fonte.tem_rss = True
        fonte.url_rss = urls_rss[0] if urls_rss else None

    await db.commit()

    return {
        "urls_sitemap": len(urls),
        "urls_rss": len(urls_rss),
        "novas_urls": novos,
    }


@router.get("/status")
async def status_coleta(db: AsyncSession = Depends(get_db)):
    """Retorna status geral da coleta."""
    # Conta por status
    result = await db.execute(
        select(Conteudo.status, func.count(Conteudo.id))
        .group_by(Conteudo.status)
    )
    por_status = {row[0]: row[1] for row in result.fetchall()}

    # Fontes ativas
    result_fontes = await db.execute(
        select(func.count(Fonte.id)).where(Fonte.status == FonteStatus.ATIVA.value)
    )
    fontes_ativas = result_fontes.scalar()

    # Pendentes para coletar
    pendentes = por_status.get("pendente", 0) + por_status.get(ConteudoStatus.COLETADO.value, 0)

    return {
        "fontes_ativas": fontes_ativas,
        "pendentes_coleta": pendentes,
        "conteudos_por_status": por_status,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def _executar_coleta_fonte(fonte_id: int):
    """Task background para coletar uma fonte."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            await coletar_lote(fonte_id, db)
        except Exception as e:
            from loguru import logger
            logger.error(f"Erro na coleta da fonte {fonte_id}: {e}")


async def _processar_lote_ids(ids: list[int]):
    """Task background para processar um lote de conteúdos."""
    from app.database import AsyncSessionLocal
    from loguru import logger
    async with AsyncSessionLocal() as db:
        for conteudo_id in ids:
            try:
                await processar_conteudo(conteudo_id, db)
            except Exception as e:
                logger.error(f"Erro ao processar {conteudo_id}: {e}")
        await db.commit()
