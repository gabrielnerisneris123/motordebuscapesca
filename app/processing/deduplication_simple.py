"""
Deduplicação simplificada sem dependências pesadas.
Usa apenas hashlib (built-in do Python).
"""

import hashlib
import re
from urllib.parse import urlparse, parse_qs, urlencode


def gerar_hash_conteudo(texto: str) -> str:
    """Hash SHA-256 para deduplicação exata."""
    if not texto:
        return ""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def gerar_hash_rapido(texto: str) -> str:
    """Hash MD5 para comparação rápida."""
    if not texto:
        return ""
    return hashlib.md5(texto.encode("utf-8")).hexdigest()


def gerar_simhash(texto: str) -> str:
    """Stub do SimHash - retorna hash simples."""
    if not texto or len(texto) < 50:
        return ""
    return gerar_hash_rapido(texto[:1000])


def calcular_distancia_simhash(hash1: str, hash2: str) -> int:
    """Stub - retorna distância máxima."""
    return 64


def sao_similares(hash1: str, hash2: str, limiar: int = 5) -> bool:
    """Stub - compara igualdade exata."""
    return hash1 == hash2


def gerar_fingerprint_url(url: str) -> str:
    """Gera fingerprint normalizado de URL para deduplicação."""
    if not url:
        return ""

    parsed = urlparse(url.lower().strip())

    # Remove parâmetros de rastreamento comuns
    params_ignorar = {
        "utm_source", "utm_medium", "utm_campaign", "utm_content",
        "utm_term", "fbclid", "gclid", "ref", "source", "from",
        "_ga", "mc_cid", "mc_eid",
    }

    if parsed.query:
        params = parse_qs(parsed.query)
        params_limpos = {k: v for k, v in params.items() if k.lower() not in params_ignorar}
        query_limpa = urlencode(params_limpos, doseq=True)
    else:
        query_limpa = ""

    url_normalizada = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if query_limpa:
        url_normalizada += f"?{query_limpa}"

    return url_normalizada.rstrip("/")
