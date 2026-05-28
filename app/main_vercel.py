from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
import os

from app.config_vercel import settings
from app.database_vercel import init_db
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando Motor de Busca de Pesca Esportiva (Vercel)...")
    await init_db()
    logger.info("Sistema iniciado com sucesso.")
    yield
    logger.info("Sistema encerrado.")


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
    return {"status": "ok", "version": "1.0.0", "environment": "vercel"}
