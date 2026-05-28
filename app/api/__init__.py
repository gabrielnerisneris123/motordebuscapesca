from fastapi import APIRouter
from app.api.routes import fontes, conteudos, coleta, entidades, stats

api_router = APIRouter()
api_router.include_router(fontes.router)
api_router.include_router(conteudos.router)
api_router.include_router(coleta.router)
api_router.include_router(entidades.router)
api_router.include_router(stats.router)
