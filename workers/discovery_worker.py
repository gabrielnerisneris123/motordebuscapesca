"""
Worker de descoberta contínua de novas fontes.
Executa em loop, alternando entre buscas e crawling de links.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.crawler.discovery import ciclo_descoberta, expandir_fonte
from app.models import Fonte, FonteStatus
from sqlalchemy import select


logger.add(
    "logs/discovery_worker.log",
    rotation="100 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)


async def loop_descoberta():
    """Loop principal de descoberta de fontes."""
    await init_db()
    logger.info("Worker de descoberta iniciado")

    ciclo = 0
    while True:
        ciclo += 1
        logger.info(f"=== Ciclo de descoberta #{ciclo} ===")

        try:
            async with AsyncSessionLocal() as db:
                # Ciclo de busca por novas fontes
                novas = await ciclo_descoberta(db)
                await db.commit()
                logger.info(f"Ciclo {ciclo}: {novas} novas fontes")

                # Expande fontes existentes com menor cobertura
                result = await db.execute(
                    select(Fonte)
                    .where(
                        Fonte.status == FonteStatus.ATIVA.value,
                        Fonte.paginas_coletadas < 10,
                    )
                    .order_by(Fonte.score_relevancia.desc())
                    .limit(10)
                )
                fontes_expandir = result.scalars().all()

                for fonte in fontes_expandir:
                    try:
                        urls = await expandir_fonte(fonte.id, db)
                        logger.info(f"Expandida: {fonte.dominio} → {urls} URLs")
                        await db.commit()
                    except Exception as e:
                        logger.error(f"Erro ao expandir {fonte.dominio}: {e}")
                        await db.rollback()

        except Exception as e:
            logger.error(f"Erro no ciclo {ciclo}: {e}")

        intervalo = settings.discovery_interval_minutes * 60
        logger.info(f"Aguardando {settings.discovery_interval_minutes} minutos...")
        await asyncio.sleep(intervalo)


if __name__ == "__main__":
    asyncio.run(loop_descoberta())
