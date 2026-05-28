"""Utilitários do crawler."""

from datetime import datetime
from dateutil import parser as date_parser
from loguru import logger


def parsear_data(data_str: str) -> datetime | None:
    """Tenta parsear uma string de data em vários formatos."""
    if not data_str:
        return None

    try:
        return date_parser.parse(data_str, dayfirst=True, fuzzy=True)
    except Exception:
        return None


def limpar_url(url: str) -> str:
    """Remove parâmetros de tracking de uma URL."""
    import re
    from urllib.parse import urlparse, parse_qs, urlencode

    if not url:
        return ""

    params_ignorar = {
        "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
        "fbclid", "gclid", "_ga", "mc_cid", "mc_eid", "ref",
    }

    parsed = urlparse(url)
    if parsed.query:
        params = parse_qs(parsed.query)
        params_limpos = {k: v for k, v in params.items() if k.lower() not in params_ignorar}
        query = urlencode(params_limpos, doseq=True)
    else:
        query = ""

    result = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if query:
        result += f"?{query}"

    return result.rstrip("/")


def estimar_tempo_leitura(num_palavras: int) -> int:
    """Estima tempo de leitura em minutos (250 palavras/min)."""
    return max(1, round(num_palavras / 250))
