"""
Tasks Celery para execução assíncrona e agendada.
"""

import asyncio
from loguru import logger
from app.celery_app import celery_app
from app.config import settings


def _run_async(coro):
    """Executa coroutine em contexto síncrono do Celery."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.task_ciclo_descoberta", bind=True, max_retries=3)
def task_ciclo_descoberta(self):
    """Executa ciclo de descoberta de novas fontes."""
    from app.database import AsyncSessionLocal
    from app.crawler.discovery import ciclo_descoberta

    async def _executar():
        async with AsyncSessionLocal() as db:
            total = await ciclo_descoberta(db)
            await db.commit()
            return total

    try:
        total = _run_async(_executar())
        logger.info(f"Ciclo descoberta: {total} novas fontes")
        return {"novas_fontes": total}
    except Exception as e:
        logger.error(f"Erro no ciclo descoberta: {e}")
        raise self.retry(exc=e, countdown=300)


@celery_app.task(name="app.tasks.task_coleta_todas_fontes", bind=True)
def task_coleta_todas_fontes(self):
    """Coleta conteúdo de todas as fontes ativas."""
    from app.database import AsyncSessionLocal
    from app.models import Fonte, FonteStatus
    from app.crawler.scraper import coletar_lote
    from sqlalchemy import select

    async def _executar():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Fonte).where(Fonte.status == FonteStatus.ATIVA.value)
                .order_by(Fonte.score_relevancia.desc())
                .limit(20)
            )
            fontes = result.scalars().all()

            total_coletados = 0
            for fonte in fontes:
                try:
                    stats = await coletar_lote(fonte.id, db, limite=settings.batch_size)
                    total_coletados += stats.get("sucesso", 0)
                except Exception as e:
                    logger.error(f"Erro ao coletar fonte {fonte.id}: {e}")

            return total_coletados

    try:
        total = _run_async(_executar())
        logger.info(f"Coleta todas fontes: {total} conteúdos coletados")
        return {"total_coletados": total}
    except Exception as e:
        logger.error(f"Erro na coleta geral: {e}")
        return {"erro": str(e)}


@celery_app.task(name="app.tasks.task_processar_pendentes", bind=True)
def task_processar_pendentes(self):
    """Processa conteúdos coletados mas pendentes de processamento."""
    from app.database import AsyncSessionLocal
    from app.models import Conteudo, ConteudoStatus
    from app.processing.pipeline import processar_conteudo
    from sqlalchemy import select

    async def _executar():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Conteudo.id)
                .where(Conteudo.status == ConteudoStatus.COLETADO.value)
                .limit(200)
            )
            ids = [r[0] for r in result.fetchall()]

            processados = 0
            for conteudo_id in ids:
                try:
                    sucesso = await processar_conteudo(conteudo_id, db)
                    if sucesso:
                        processados += 1
                except Exception as e:
                    logger.error(f"Erro ao processar {conteudo_id}: {e}")

            await db.commit()
            return processados

    try:
        total = _run_async(_executar())
        logger.info(f"Processados {total} conteúdos pendentes")
        return {"processados": total}
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        return {"erro": str(e)}


@celery_app.task(name="app.tasks.task_limpar_logs", bind=True)
def task_limpar_logs(self):
    """Remove logs com mais de 30 dias."""
    from app.database import AsyncSessionLocal
    from app.models import LogColeta
    from sqlalchemy import delete
    from datetime import datetime, timedelta

    async def _executar():
        async with AsyncSessionLocal() as db:
            limite = datetime.utcnow() - timedelta(days=30)
            result = await db.execute(
                delete(LogColeta).where(LogColeta.data_hora < limite)
            )
            await db.commit()
            return result.rowcount

    total = _run_async(_executar())
    logger.info(f"Logs removidos: {total}")
    return {"removidos": total}


@celery_app.task(name="app.tasks.task_coletar_fonte", bind=True, max_retries=2)
def task_coletar_fonte(self, fonte_id: int):
    """Coleta conteúdo de uma fonte específica."""
    from app.database import AsyncSessionLocal
    from app.crawler.scraper import coletar_lote

    async def _executar():
        async with AsyncSessionLocal() as db:
            return await coletar_lote(fonte_id, db)

    try:
        stats = _run_async(_executar())
        return stats
    except Exception as e:
        raise self.retry(exc=e, countdown=60)
