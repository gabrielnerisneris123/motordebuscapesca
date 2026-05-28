"""
Exporta o dataset completo para CSV/JSONL para treinamento de modelos.
Execute: python scripts/exportar_dataset.py
"""

import asyncio
import sys
import os
import json
import csv
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from sqlalchemy import select
from app.database import init_db, AsyncSessionLocal
from app.models import Conteudo, ConteudoStatus


async def exportar_csv(output_path: str = "dataset_pesca.csv"):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Conteudo)
            .where(
                Conteudo.status == ConteudoStatus.PROCESSADO.value,
                Conteudo.score_relevancia >= 1.0,
                Conteudo.num_palavras >= 50,
            )
            .order_by(Conteudo.score_relevancia.desc())
        )
        conteudos = result.scalars().all()

    logger.info(f"Exportando {len(conteudos)} conteúdos para CSV...")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "url", "titulo", "conteudo", "autor",
            "data_publicacao", "data_coleta", "num_palavras",
            "score_relevancia", "tags", "categorias",
        ])
        for c in conteudos:
            writer.writerow([
                c.id, c.url, c.titulo or "",
                (c.conteudo_texto or "").replace("\n", " "),
                c.autor or "",
                c.data_publicacao.isoformat() if c.data_publicacao else "",
                c.data_coleta.isoformat(),
                c.num_palavras, c.score_relevancia,
                "|".join(c.tags or []),
                "|".join(c.categorias or []),
            ])

    logger.info(f"CSV exportado: {output_path}")


async def exportar_jsonl(output_path: str = "dataset_pesca.jsonl"):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Conteudo)
            .where(
                Conteudo.status == ConteudoStatus.PROCESSADO.value,
                Conteudo.score_relevancia >= 1.0,
                Conteudo.num_palavras >= 50,
            )
            .order_by(Conteudo.score_relevancia.desc())
        )
        conteudos = result.scalars().all()

    logger.info(f"Exportando {len(conteudos)} conteúdos para JSONL...")

    with open(output_path, "w", encoding="utf-8") as f:
        for c in conteudos:
            obj = {
                "id": c.id,
                "url": c.url,
                "titulo": c.titulo,
                "texto": c.conteudo_texto,
                "autor": c.autor,
                "data_publicacao": c.data_publicacao.isoformat() if c.data_publicacao else None,
                "data_coleta": c.data_coleta.isoformat(),
                "num_palavras": c.num_palavras,
                "score_relevancia": c.score_relevancia,
                "tags": c.tags or [],
                "categorias": c.categorias or [],
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    logger.info(f"JSONL exportado: {output_path}")


async def main():
    await init_db()
    await exportar_csv()
    await exportar_jsonl()


if __name__ == "__main__":
    asyncio.run(main())
