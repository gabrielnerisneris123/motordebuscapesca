"""
Script para rodar o projeto localmente sem Docker.
Usa SQLite em vez de PostgreSQL.

Como usar:
    python run_local.py

Acesse:
    http://localhost:8001
    http://localhost:8001/docs
"""

import sys
import os

# Set env vars para modo local
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./motordebusca.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./motordebusca.db"
os.environ["APP_ENV"] = "development"
os.environ["DEBUG"] = "true"
os.environ["REDIS_URL"] = ""

# Injeta os módulos substitutos
import app.database_vercel as _database_vercel
import app.config_vercel as _config_vercel
import app.celery_app_vercel as _celery_app_vercel
import app.tasks_vercel as _tasks_vercel
import app.crawler.scraper_vercel as _scraper_vercel
import app.processing.deduplication_simple as _dedup_simple

sys.modules["app.database"] = _database_vercel
sys.modules["app.config"] = _config_vercel
sys.modules["app.celery_app"] = _celery_app_vercel
sys.modules["app.tasks"] = _tasks_vercel
sys.modules["app.crawler.scraper"] = _scraper_vercel
sys.modules["app.processing.deduplication"] = _dedup_simple

# Importa os modelos para registrar no metadata
from app.models import fonte, conteudo, entidade, log

# Cria o banco de dados
import asyncio
from app.database_vercel import init_db
asyncio.run(init_db())

# Importa e roda o app
from app.main_vercel import app

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("Motor de Busca - Pesca Esportiva")
    print("=" * 50)
    print("")
    print("Acesse: http://localhost:8001")
    print("Docs:   http://localhost:8001/docs")
    print("")
    print("Pressione CTRL+C para parar")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
