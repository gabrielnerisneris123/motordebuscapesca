from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.database import get_db
from app.models import Fonte, Conteudo, Entidade, LogColeta
from app.schemas.stats import EstatisticasGerais

router = APIRouter(prefix="/stats", tags=["Estatísticas"])


@router.get("", response_model=EstatisticasGerais)
async def estatisticas_gerais(db: AsyncSession = Depends(get_db)):
    """Retorna estatísticas gerais do sistema."""

    # Fontes
    r = await db.execute(select(func.count(Fonte.id)))
    total_fontes = r.scalar() or 0

    r = await db.execute(select(func.count(Fonte.id)).where(Fonte.status == "ativa"))
    fontes_ativas = r.scalar() or 0

    r = await db.execute(
        select(Fonte.status, func.count(Fonte.id)).group_by(Fonte.status)
    )
    fontes_por_status = {row[0]: row[1] for row in r.fetchall()}

    # Conteúdos
    r = await db.execute(select(func.count(Conteudo.id)))
    total_conteudos = r.scalar() or 0

    r = await db.execute(
        select(func.count(Conteudo.id)).where(Conteudo.status == "processado")
    )
    conteudos_processados = r.scalar() or 0

    r = await db.execute(
        select(func.count(Conteudo.id)).where(Conteudo.status == "duplicado")
    )
    conteudos_duplicados = r.scalar() or 0

    r = await db.execute(
        select(Conteudo.status, func.count(Conteudo.id)).group_by(Conteudo.status)
    )
    conteudos_por_status = {row[0]: row[1] for row in r.fetchall()}

    # Entidades
    r = await db.execute(select(func.count(Entidade.id)))
    total_entidades = r.scalar() or 0

    # Total palavras
    r = await db.execute(select(func.coalesce(func.sum(Conteudo.num_palavras), 0)))
    total_palavras = r.scalar() or 0

    return EstatisticasGerais(
        total_fontes=total_fontes,
        fontes_ativas=fontes_ativas,
        total_conteudos=total_conteudos,
        conteudos_processados=conteudos_processados,
        conteudos_duplicados=conteudos_duplicados,
        total_entidades=total_entidades,
        total_palavras=total_palavras,
        fontes_por_status=fontes_por_status,
        conteudos_por_status=conteudos_por_status,
    )


@router.get("/logs")
async def listar_logs(
    tipo: str = None,
    limite: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Retorna logs recentes de coleta."""
    query = select(LogColeta).order_by(LogColeta.data_hora.desc()).limit(limite)
    if tipo:
        query = query.where(LogColeta.tipo == tipo)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "id": l.id,
            "tipo": l.tipo,
            "mensagem": l.mensagem,
            "url": l.url,
            "data_hora": l.data_hora.isoformat() if l.data_hora else None,
            "worker": l.worker,
        }
        for l in logs
    ]


@router.get("/crescimento")
async def crescimento_diario(
    dias: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Retorna crescimento diário de conteúdos."""
    result = await db.execute(
        text("""
            SELECT DATE(data_coleta) as dia, COUNT(*) as total
            FROM conteudos
            WHERE data_coleta >= NOW() - INTERVAL ':dias days'
            GROUP BY DATE(data_coleta)
            ORDER BY dia
        """).bindparams(dias=dias)
    )
    return [{"dia": str(row[0]), "total": row[1]} for row in result.fetchall()]
