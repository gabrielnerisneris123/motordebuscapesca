from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    secret_key: str = "mude-esta-chave-em-producao"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://admin:admin123@localhost:5432/motordebusca"
    database_url_sync: str = "postgresql://admin:admin123@localhost:5432/motordebusca"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Crawler
    crawl_delay_min: float = 1.0
    crawl_delay_max: float = 4.0
    max_concurrent_requests: int = 10
    max_pages_per_domain: int = 500
    request_timeout: int = 30
    max_retries: int = 3

    # Playwright
    playwright_headless: bool = True
    playwright_timeout: int = 30000

    # Worker
    discovery_interval_minutes: int = 60
    scraper_workers: int = 4
    batch_size: int = 50

    # Search
    search_queries_per_cycle: int = 20
    max_search_results: int = 50

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
