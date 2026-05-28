"""
Configuração adaptada para deploy no Vercel (serverless).
Usa SQLite em vez de PostgreSQL e desabilita componentes que não funcionam no serverless.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class VercelSettings(BaseSettings):
    # App
    app_env: str = "production"
    secret_key: str = "vercel-deploy-key"
    debug: bool = False

    # Database - SQLite no /tmp (único local gravável no Vercel)
    database_url: str = "sqlite+aiosqlite:///tmp/motordebusca.db"
    database_url_sync: str = "sqlite:///tmp/motordebusca.db"

    # Redis - desabilitado no serverless
    redis_url: str = ""

    # Crawler - limitado no serverless
    crawl_delay_min: float = 1.0
    crawl_delay_max: float = 3.0
    max_concurrent_requests: int = 3
    max_pages_per_domain: int = 50
    request_timeout: int = 15
    max_retries: int = 2

    # Playwright - desabilitado no serverless (não suportado)
    playwright_headless: bool = True
    playwright_timeout: int = 15000

    # Worker - desabilitado no serverless
    discovery_interval_minutes: int = 60
    scraper_workers: int = 1
    batch_size: int = 10

    # Search
    search_queries_per_cycle: int = 5
    max_search_results: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> VercelSettings:
    return VercelSettings()


settings = get_settings()
