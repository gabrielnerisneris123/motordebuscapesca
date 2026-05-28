"""
Configuração do Celery para tarefas agendadas e distribuídas.
"""

from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "motordebusca",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        # Descoberta de novas fontes a cada 6 horas
        "descoberta-fontes": {
            "task": "app.tasks.task_ciclo_descoberta",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        # Coleta contínua a cada 30 minutos
        "coleta-conteudos": {
            "task": "app.tasks.task_coleta_todas_fontes",
            "schedule": crontab(minute="*/30"),
        },
        # Processamento de pendentes a cada 15 minutos
        "processamento-pendentes": {
            "task": "app.tasks.task_processar_pendentes",
            "schedule": crontab(minute="*/15"),
        },
        # Limpeza de logs antigos às 2h da manhã
        "limpeza-logs": {
            "task": "app.tasks.task_limpar_logs",
            "schedule": crontab(hour=2, minute=0),
        },
    },
)
