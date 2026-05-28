"""
Worker de scraping contínuo.
Coleta e processa conteúdos de todas as fontes ativas em paralelo.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.crawler.scraper import coletar_e_salvar
from app.processing.pipeline import processar_conteudo
from app.models import Conteudo, Fonte, FonteStatus, ConteudoStatus
from sqlalchemy import select, update


logger.add(
    "logs/scraper_worker.log",
    rotation="100 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)


async def buscar_pendentes(db, limite: int = 100) -> list[int]:
    """Busca IDs de conteúdos pendentes de coleta."""
    result = await db.execute(
        select(Conteudo.id)
        .join(Fonte, Conteudo.fonte_id == Fonte.id)
        .where(
            Conteudo.status == "pendente",
            Fonte.status == FonteStatus.ATIVA.value,
        )
        .order_by(Fonte.score_relevancia.desc())
        .limit(limite)
    )
    return [r[0] for r in result.fetchall()]


async def processar_batch_coleta(ids: list[int]) -> dict:
    """Coleta um batch de URLs em paralelo."""
    semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
    stats = {"coletados": 0, "erros": 0, "duplicados": 0}

    async def _coletar_um(conteudo_id: int):
        async with semaphore:
            async with AsyncSessionLocal() as db:
                try:
                    sucesso = await coletar_e_salvar(conteudo_id, db)
                    await db.commit()

                    # Verifica status após coleta
                    result = await db.execute(
                        select(Conteudo).where(Conteudo.id == conteudo_id)
                    )
                    c = result.scalar_one_or_none()
                    if c:
                        if c.status == ConteudoStatus.DUPLICADO.value:
                            stats["duplicados"] += 1
                        elif sucesso:
                            stats["coletados"] += 1
                        else:
                            stats["erros"] += 1
                except Exception as e:
                    logger.error(f"Erro ao coletar {conteudo_id}: {e}")
                    stats["erros"] += 1

    await asyncio.gather(*[_coletar_um(id) for id in ids])
    return stats


async def processar_batch_processamento(limite: int = 200) -> int:
    """Processa conteúdos coletados mas não processados."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Conteudo.id)
            .where(Conteudo.status == ConteudoStatus.COLETADO.value)
            .limit(limite)
        )
        ids = [r[0] for r in result.fetchall()]

    processados = 0
    for conteudo_id in ids:
        async with AsyncSessionLocal() as db:
            try:
                sucesso = await processar_conteudo(conteudo_id, db)
                await db.commit()
                if sucesso:
                    processados += 1
            except Exception as e:
                logger.error(f"Erro ao processar {conteudo_id}: {e}")

    return processados


async def loop_scraper():
    """Loop principal do worker de scraping."""
    await init_db()
    logger.info(f"Worker scraper iniciado | max_concurrent={settings.max_concurrent_requests}")

    ciclo = 0
    while True:
        ciclo += 1
        logger.info(f"=== Ciclo scraping #{ciclo} ===")

        try:
            # Fase 1: Coleta
            async with AsyncSessionLocal() as db:
                ids_pendentes = await buscar_pendentes(db, limite=settings.batch_size)

            if ids_pendentes:
                logger.info(f"Coletando {len(ids_pendentes)} URLs...")
                stats = await processar_batch_coleta(ids_pendentes)
                logger.info(f"Coleta: {stats}")
            else:
                logger.info("Nenhum conteúdo pendente para coletar")

            # Fase 2: Processamento
            logger.info("Processando conteúdos coletados...")
            processados = await processar_batch_processamento(limite=200)
            logger.info(f"Processados: {processados} conteúdos")

        except Exception as e:
            logger.error(f"Erro no ciclo scraper {ciclo}: {e}")

        # Se não há pendentes, aguarda mais
        if not ids_pendentes:
            await asyncio.sleep(60)
        else:
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(loop_scraper())
