"""
Entrypoint para deploy no Vercel (Serverless Functions).
Adapta o app FastAPI para funcionar no ambiente serverless.
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===== SET ENV VARS ANTES DE QUALQUER IMPORT =====
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///tmp/motordebusca.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///tmp/motordebusca.db"
os.environ["APP_ENV"] = "production"
os.environ["DEBUG"] = "false"
os.environ["REDIS_URL"] = ""

# ===== PREPARA OS MÓDULOS SUBSTITUTOS =====
import app.database_vercel as _database_vercel
import app.config_vercel as _config_vercel
import app.celery_app_vercel as _celery_app_vercel
import app.tasks_vercel as _tasks_vercel
import app.crawler.scraper_vercel as _scraper_vercel

# Injeta os módulos substitutos no sys.modules ANTES de qualquer outro import
sys.modules["app.database"] = _database_vercel
sys.modules["app.config"] = _config_vercel
sys.modules["app.celery_app"] = _celery_app_vercel
sys.modules["app.tasks"] = _tasks_vercel
sys.modules["app.crawler.scraper"] = _scraper_vercel

# ===== IMPORTA OS MODELOS (agora usarão o Base do database_vercel) =====
from app.models import fonte, conteudo, entidade, log

# ===== IMPORTA O APP PRINCIPAL =====
from app.main_vercel import app

# ===== HANDLER PARA VERCEL =====
from mangum import Mangum

handler = Mangum(app, lifespan="off")
