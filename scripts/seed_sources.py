"""
Script para seed manual de fontes conhecidas de pesca esportiva.
Execute: python scripts/seed_sources.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from app.database import init_db, AsyncSessionLocal
from app.crawler.discovery import cadastrar_fonte
from app.classifier.keywords import SEEDS_FONTES


# Fontes adicionais para seed manual
FONTES_EXTRAS = [
    ("https://www.pescaeaqua.com.br", "Pesca e Água"),
    ("https://www.carpabrasil.com.br", "Carpa Brasil"),
    ("https://www.revistapescaesportiva.com.br", "Revista Pesca Esportiva"),
    ("https://www.fishingbrasil.com.br", "Fishing Brasil"),
    ("https://www.pesqueiro.com.br", "Pesqueiro"),
    ("https://www.tunapesca.com.br", "Tuna Pesca"),
    ("https://forum.pescaesportiva.net", "Fórum Pesca Esportiva"),
    ("https://www.blogdopescador.com.br", "Blog do Pescador"),
    ("https://www.carpfishing.com.br", "Carp Fishing"),
]


async def main():
    logger.info("Iniciando seed de fontes...")
    await init_db()

    async with AsyncSessionLocal() as db:
        total = 0
        for url, nome in FONTES_EXTRAS:
            try:
                fonte = await cadastrar_fonte(url, db, descoberta_via="seed_manual", nome=nome)
                if fonte:
                    total += 1
                    logger.info(f"✓ {nome} — score={fonte.score_relevancia:.1f}")
                else:
                    logger.warning(f"✗ Falhou: {url}")
            except Exception as e:
                logger.error(f"Erro em {url}: {e}")

        await db.commit()
        logger.info(f"Seed concluído: {total} fontes cadastradas")


if __name__ == "__main__":
    asyncio.run(main())
