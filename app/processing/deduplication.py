"""
Sistema de deduplicação com hash exato e SimHash para conteúdo similar.
"""

import hashlib
import xxhash
from simhash import Simhash
from loguru import logger


def gerar_hash_conteudo(texto: str) -> str:
    """Hash SHA-256 para deduplicação exata."""
    if not texto:
        return ""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def gerar_hash_rapido(texto: str) -> str:
    """Hash xxhash para comparação rápida."""
    if not texto:
        return ""
    return xxhash.xxh64(texto.encode("utf-8")).hexdigest()


def gerar_simhash(texto: str) -> str:
    """Gera SimHash para detecção de conteúdo similar."""
    if not texto or len(texto) < 50:
        return ""
    try:
        sh = Simhash(texto)
        return str(sh.value)
    except Exception as e:
        logger.warning(f"Erro ao gerar SimHash: {e}")
        return ""


def calcular_distancia_simhash(hash1: str, hash2: str) -> int:
    """Calcula distância de Hamming entre dois SimHashes."""
    if not hash1 or not hash2:
        return 64

    try:
        s1 = Simhash(int(hash1))
        s2 = Simhash(int(hash2))
        return s1.distance(s2)
    except Exception:
        return 64


def sao_similares(hash1: str, hash2: str, limiar: int = 5) -> bool:
    """
    Verifica se dois conteúdos são similares baseado no SimHash.
    Limiar padrão de 5 bits (de 64) = ~92% similar.
    """
    distancia = calcular_distancia_simhash(hash1, hash2)
    return distancia <= limiar


def gerar_fingerprint_url(url: str) -> str:
    """Gera fingerprint normalizado de URL para deduplicação."""
    import re
    from urllib.parse import urlparse, parse_qs, urlencode

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
