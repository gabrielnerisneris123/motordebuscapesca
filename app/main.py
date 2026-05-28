from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
import os

from app.config import settings
from app.database import init_db
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando Motor de Busca de Pesca Esportiva...")
    await init_db()
    await _seed_fontes_iniciais()
    logger.info("Sistema iniciado com sucesso.")
    yield
    logger.info("Sistema encerrado.")


async def _seed_fontes_iniciais():
    """Cadastra fontes seed se o banco estiver vazio."""
    from app.database import AsyncSessionLocal
    from app.models import Fonte
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.count(Fonte.id)))
        total = result.scalar()

        if total == 0:
            from app.classifier.keywords import SEEDS_FONTES
            from app.crawler.discovery import cadastrar_fonte
            logger.info("Cadastrando fontes seed iniciais...")
            for url in SEEDS_FONTES[:5]:  # Limita para não demorar no boot
                try:
                    await cadastrar_fonte(url, db, descoberta_via="seed")
                except Exception as e:
                    logger.warning(f"Falha ao cadastrar seed {url}: {e}")
            await db.commit()
            logger.info("Seeds cadastradas.")


app = FastAPI(
    title="Motor de Busca - Pesca Esportiva Brasileira",
    description="Plataforma de coleta massiva de dados sobre pesca esportiva",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api/v1")

# Dashboard estático
static_path = os.path.join(os.path.dirname(__file__), "dashboard", "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/")
async def dashboard():
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "ok", "mensagem": "Motor de Busca - Pesca Esportiva"}


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
