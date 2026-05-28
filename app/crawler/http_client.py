"""
Cliente HTTP com retry, rate limiting e rotação de User-Agent.
"""

import asyncio
import random
import time
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from fake_useragent import UserAgent
from loguru import logger
from app.config import settings

_ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

# Rate limiter por domínio
_ultimo_request: dict[str, float] = {}
_lock_dominio: dict[str, asyncio.Lock] = {}


def _get_lock(dominio: str) -> asyncio.Lock:
    if dominio not in _lock_dominio:
        _lock_dominio[dominio] = asyncio.Lock()
    return _lock_dominio[dominio]


async def _respeitar_rate_limit(dominio: str) -> None:
    """Garante intervalo mínimo entre requests ao mesmo domínio."""
    lock = _get_lock(dominio)
    async with lock:
        ultimo = _ultimo_request.get(dominio, 0)
        decorrido = time.time() - ultimo
        delay = random.uniform(settings.crawl_delay_min, settings.crawl_delay_max)

        if decorrido < delay:
            await asyncio.sleep(delay - decorrido)

        _ultimo_request[dominio] = time.time()


def _headers_padrao() -> dict:
    return {
        "User-Agent": _ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }


async def fetch_url(
    url: str,
    timeout: int = None,
    headers: dict = None,
    follow_redirects: bool = True,
    max_retries: int = None,
) -> Optional[tuple[str, int, str]]:
    """
    Faz GET em uma URL respeitando rate limit.
    Retorna: (html, status_code, url_final) ou None em caso de erro.
    """
    from urllib.parse import urlparse
    dominio = urlparse(url).netloc
    timeout = timeout or settings.request_timeout
    max_retries = max_retries or settings.max_retries

    await _respeitar_rate_limit(dominio)

    hdrs = _headers_padrao()
    if headers:
        hdrs.update(headers)

    for tentativa in range(max_retries):
        try:
            async with httpx.AsyncClient(
                follow_redirects=follow_redirects,
                timeout=httpx.Timeout(timeout),
                limits=httpx.Limits(max_keepalive_connections=20),
            ) as client:
                response = await client.get(url, headers=hdrs)

                if response.status_code == 200:
                    # Detecta encoding
                    content_type = response.headers.get("content-type", "")
                    if "text/html" not in content_type and "text/plain" not in content_type:
                        return None

                    try:
                        html = response.text
                    except Exception:
                        html = response.content.decode("utf-8", errors="replace")

                    return html, response.status_code, str(response.url)

                elif response.status_code in (301, 302, 303, 307, 308):
                    # Redirecionamento já tratado pelo follow_redirects
                    return None
                elif response.status_code == 429:
                    wait = int(response.headers.get("retry-after", 60))
                    logger.warning(f"Rate limit em {dominio}, aguardando {wait}s")
                    await asyncio.sleep(wait)
                elif response.status_code in (403, 404, 410):
                    return None
                else:
                    logger.warning(f"Status {response.status_code} para {url}")
                    return None

        except httpx.TimeoutException:
            if tentativa < max_retries - 1:
                await asyncio.sleep(2 ** tentativa)
            else:
                logger.warning(f"Timeout após {max_retries} tentativas: {url}")
        except httpx.TooManyRedirects:
            logger.warning(f"Muitos redirecionamentos: {url}")
            return None
        except Exception as e:
            if tentativa < max_retries - 1:
                await asyncio.sleep(2 ** tentativa)
            else:
                logger.error(f"Erro ao buscar {url}: {e}")

    return None


async def check_robots_txt(dominio: str) -> str:
    """Baixa e retorna o conteúdo do robots.txt."""
    for scheme in ("https", "http"):
        resultado = await fetch_url(f"{scheme}://{dominio}/robots.txt", timeout=10, max_retries=1)
        if resultado:
            html, status, _ = resultado
            return html
    return ""


def is_url_permitida(url: str, robots_txt: str) -> bool:
    """Verifica se a URL é permitida pelo robots.txt."""
    if not robots_txt:
        return True

    from urllib.parse import urlparse
    path = urlparse(url).path

    linhas = robots_txt.lower().split("\n")
    agente_valido = False

    for linha in linhas:
        linha = linha.strip()
        if linha.startswith("user-agent:"):
            agente = linha.split(":", 1)[1].strip()
            agente_valido = agente in ("*", "googlebot")
        elif agente_valido and linha.startswith("disallow:"):
            caminho_proibido = linha.split(":", 1)[1].strip()
            if caminho_proibido and path.startswith(caminho_proibido):
                return False

    return True
