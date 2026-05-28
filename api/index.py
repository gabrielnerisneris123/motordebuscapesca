"""
Entrypoint para deploy no Vercel (Serverless Functions).
Suporta tanto SQLite local quanto PostgreSQL (Supabase).
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===== SET ENV VARS PADRÃO =====
# Se não houver DATABASE_URL do Supabase, usa SQLite
os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("REDIS_URL", "")

# Se não tiver DATABASE_URL configurado (Supabase), usa SQLite
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///tmp/motordebusca.db"
    os.environ["DATABASE_URL_SYNC"] = "sqlite:///tmp/motordebusca.db"

try:
    # Detecta se é PostgreSQL (Supabase) ou SQLite
    db_url = os.environ.get("DATABASE_URL", "")
    
    if "postgresql" in db_url or "postgres" in db_url:
        # Usa o módulo Supabase (PostgreSQL)
        import app.database_supabase as _database
    else:
        # Usa o módulo SQLite (Vercel local)
        import app.database_vercel as _database
    
    import app.config_vercel as _config_vercel
    import app.celery_app_vercel as _celery_app_vercel
    import app.tasks_vercel as _tasks_vercel
    import app.crawler.scraper_vercel as _scraper_vercel

    # Injeta os módulos substitutos no sys.modules
    sys.modules["app.database"] = _database
    sys.modules["app.config"] = _config_vercel
    sys.modules["app.celery_app"] = _celery_app_vercel
    sys.modules["app.tasks"] = _tasks_vercel
    sys.modules["app.crawler.scraper"] = _scraper_vercel

    # ===== IMPORTA OS MODELOS =====
    from app.models import fonte, conteudo, entidade, log

    # ===== IMPORTA O APP PRINCIPAL =====
    from app.main_vercel import app

    # ===== HANDLER PARA VERCEL =====
    from mangum import Mangum

    handler = Mangum(app, lifespan="off")

except Exception as e:
    import traceback
    error_msg = f"Erro na inicialização: {str(e)}\n{traceback.format_exc()}"
    
    # Cria um app mínimo que retorna o erro
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    
    @app.get("/{path:path}")
    async def error_handler(path: str = ""):
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )
    
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
