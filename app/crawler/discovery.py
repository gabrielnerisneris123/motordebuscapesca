"""
Sistema de descoberta automática de fontes de pesca esportiva brasileira.
Usa DuckDuckGo, Bing, busca em sitemaps e crawling de links.
"""

import asyncio
import re
from datetime import datetime
from urllib.parse import urlparse, urljoin
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crawler.http_client import fetch_url, check_robots_txt
from app.models import Fonte, FonteStatus
from app.processing.cleaner import extrair_links
from app.classifier.keywords import SEEDS_FONTES, QUERIES_BUSCA, TERMOS_RELEVANCIA


# Domínios a ignorar (redes sociais, plataformas de vídeo, etc.)
DOMINIOS_IGNORAR = {
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "tiktok.com", "youtube.com", "youtu.be", "google.com",
    "google.com.br", "bing.com", "yahoo.com", "amazon.com",
    "amazon.com.br", "mercadolivre.com.br", "americanas.com.br",
    "shopee.com.br", "aliexpress.com", "ebay.com",
    "wikipedia.org", "wikimedia.org", "reddit.com",
}

# Extensões de arquivo a ignorar
EXTENSOES_IGNORAR = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".tar", ".gz", ".mp3", ".mp4", ".avi",
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
    ".css", ".js", ".json", ".xml", ".txt", ".csv",
}


def extrair_dominio(url: str) -> str:
    """Extrai domínio base de uma URL."""
    parsed = urlparse(url)
    return parsed.netloc.lower().replace("www.", "")


def url_valida_para_coleta(url: str) -> bool:
    """Verifica se a URL deve ser coletada."""
    if not url or len(url) > 2000:
        return False

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False

    dominio = parsed.netloc.lower().replace("www.", "")

    if any(dominio.endswith(d) or dominio == d for d in DOMINIOS_IGNORAR):
        return False

    path = parsed.path.lower()
    if any(path.endswith(ext) for ext in EXTENSOES_IGNORAR):
        return False

    return True


def calcular_relevancia_dominio(url: str, titulo: str = "", html: str = "") -> float:
    """Calcula score de relevância de uma fonte."""
    score = 0.0
    texto = f"{url} {titulo} {html[:2000]}".lower()

    for termo in TERMOS_RELEVANCIA:
        if termo in texto:
            score += 1.0

    # Bônus por termos no domínio
    dominio = extrair_dominio(url)
    termos_dominio = ["pesca", "fish", "carpa", "carp", "isco", "anzol", "pesqueiro"]
    for t in termos_dominio:
        if t in dominio:
            score += 3.0

    return min(10.0, score)


async def buscar_duckduckgo(query: str, max_resultados: int = 20) -> list[str]:
    """
    Busca no DuckDuckGo HTML (sem API) e extrai URLs dos resultados.
    """
    urls = []
    query_encoded = query.replace(" ", "+")

    # DuckDuckGo HTML
    url_busca = f"https://html.duckduckgo.com/html/?q={query_encoded}&kl=br-pt"

    resultado = await fetch_url(
        url_busca,
        headers={"Accept-Language": "pt-BR,pt;q=0.9"},
        timeout=30,
    )

    if not resultado:
        return urls

    html, _, _ = resultado

    # Extrai resultados do DDG
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")

    for link in soup.find_all("a", class_=re.compile(r"result__url|result__a", re.I)):
        href = link.get("href", "")
        if href and href.startswith("http"):
            if url_valida_para_coleta(href):
                urls.append(href)

    # Fallback: extrai qualquer link de resultado
    if not urls:
        for link in soup.find_all("a", href=re.compile(r"^https?://", re.I)):
            href = link.get("href", "")
            if url_valida_para_coleta(href):
                urls.append(href)

    logger.info(f"DuckDuckGo '{query}': {len(urls)} URLs encontradas")
    return urls[:max_resultados]


async def buscar_bing(query: str, max_resultados: int = 20) -> list[str]:
    """Busca no Bing HTML e extrai URLs dos resultados."""
    import urllib.parse
    urls = []
    query_encoded = urllib.parse.quote(query)

    url_busca = f"https://www.bing.com/search?q={query_encoded}&setlang=pt-BR&cc=BR"

    resultado = await fetch_url(
        url_busca,
        headers={
            "Accept-Language": "pt-BR,pt;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
        timeout=30,
    )

    if not resultado:
        return urls

    html, _, _ = resultado

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")

    for li in soup.find_all("li", class_=re.compile(r"b_algo")):
        link = li.find("a", href=True)
        if link:
            href = link["href"]
            if href.startswith("http") and url_valida_para_coleta(href):
                urls.append(href)

    logger.info(f"Bing '{query}': {len(urls)} URLs encontradas")
    return urls[:max_resultados]


async def descobrir_sitemap(fonte_url: str) -> list[str]:
    """Tenta encontrar e parsear o sitemap de uma fonte."""
    urls = []
    dominio_completo = urlparse(fonte_url)
    base = f"{dominio_completo.scheme}://{dominio_completo.netloc}"

    urls_sitemap_candidatas = [
        f"{base}/sitemap.xml",
        f"{base}/sitemap_index.xml",
        f"{base}/sitemap.xml.gz",
        f"{base}/wp-sitemap.xml",
        f"{base}/news-sitemap.xml",
    ]

    for url_sitemap in urls_sitemap_candidatas:
        resultado = await fetch_url(url_sitemap, timeout=15, max_retries=1)
        if not resultado:
            continue

        html, status, _ = resultado
        if not html:
            continue

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml-xml")

        # Sitemap index
        for sitemap in soup.find_all("sitemap"):
            loc = sitemap.find("loc")
            if loc:
                sub_resultado = await fetch_url(loc.text.strip(), timeout=15, max_retries=1)
                if sub_resultado:
                    sub_html, _, _ = sub_resultado
                    sub_soup = BeautifulSoup(sub_html, "lxml-xml")
                    for url_tag in sub_soup.find_all("url"):
                        loc_tag = url_tag.find("loc")
                        if loc_tag and url_valida_para_coleta(loc_tag.text.strip()):
                            urls.append(loc_tag.text.strip())

        # Sitemap direto
        for url_tag in soup.find_all("url"):
            loc_tag = url_tag.find("loc")
            if loc_tag and url_valida_para_coleta(loc_tag.text.strip()):
                urls.append(loc_tag.text.strip())

        if urls:
            logger.info(f"Sitemap encontrado em {url_sitemap}: {len(urls)} URLs")
            break

    return list(set(urls))


async def descobrir_rss(fonte_url: str) -> list[str]:
    """Tenta encontrar feeds RSS e extrai links de artigos."""
    urls = []
    dominio_completo = urlparse(fonte_url)
    base = f"{dominio_completo.scheme}://{dominio_completo.netloc}"

    # Tenta endpoints comuns de RSS
    urls_rss = [
        f"{base}/feed",
        f"{base}/rss",
        f"{base}/feed.xml",
        f"{base}/rss.xml",
        f"{base}/atom.xml",
        f"{base}/?feed=rss2",
    ]

    for url_rss in urls_rss:
        resultado = await fetch_url(url_rss, timeout=15, max_retries=1)
        if not resultado:
            continue

        html, _, _ = resultado

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml-xml")

        for item in soup.find_all(["item", "entry"]):
            link = item.find("link")
            if link:
                href = link.get("href") or link.text
                if href and url_valida_para_coleta(href.strip()):
                    urls.append(href.strip())

        if urls:
            logger.info(f"RSS encontrado em {url_rss}: {len(urls)} artigos")
            break

    return list(set(urls))


async def cadastrar_fonte(
    url: str,
    db: AsyncSession,
    descoberta_via: str = "busca",
    nome: str = "",
) -> Fonte | None:
    """
    Cadastra uma nova fonte se ainda não existir.
    Verifica robots.txt e calcula relevância.
    """
    from app.processing.deduplication import gerar_fingerprint_url
    url = gerar_fingerprint_url(url)

    if not url or not url_valida_para_coleta(url):
        return None

    dominio = extrair_dominio(url)

    # Verifica se já existe
    result = await db.execute(select(Fonte).where(Fonte.url == url))
    existente = result.scalar_one_or_none()
    if existente:
        return existente

    # Verifica robots.txt
    robots = await check_robots_txt(dominio)

    # Testa se a URL está acessível
    resultado = await fetch_url(url, timeout=15, max_retries=1)
    if not resultado:
        return None

    html, status, url_final = resultado

    score = calcular_relevancia_dominio(url, nome, html[:5000])

    fonte = Fonte(
        url=url_final,
        dominio=dominio,
        nome=nome or dominio,
        status=FonteStatus.ATIVA.value if score >= 2.0 else FonteStatus.PENDENTE.value,
        score_relevancia=score,
        robots_txt=robots[:5000] if robots else None,
        descoberta_via=descoberta_via,
        data_descoberta=datetime.utcnow(),
    )

    db.add(fonte)
    await db.flush()

    logger.info(f"Nova fonte: {dominio} | score={score:.1f} | via={descoberta_via}")
    return fonte


async def ciclo_descoberta(db: AsyncSession, queries: list[str] = None) -> int:
    """
    Executa um ciclo completo de descoberta de fontes.
    Retorna número de novas fontes encontradas.
    """
    if not queries:
        queries = QUERIES_BUSCA

    novas_fontes = 0
    todas_urls = set()

    # Seeds iniciais
    for url in SEEDS_FONTES:
        todas_urls.add(url)

    # Busca via DuckDuckGo e Bing
    for query in queries[:settings.search_queries_per_cycle]:
        try:
            urls_ddg = await buscar_duckduckgo(query, max_resultados=settings.max_search_results)
            urls_bing = await buscar_bing(query, max_resultados=settings.max_search_results)

            for url in urls_ddg + urls_bing:
                # Extrai domínio base para cadastrar como fonte
                parsed = urlparse(url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                todas_urls.add(base_url)
                todas_urls.add(url)

            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Erro na busca '{query}': {e}")

    # Cadastra fontes encontradas
    for url in todas_urls:
        try:
            fonte = await cadastrar_fonte(url, db, descoberta_via="busca_automatica")
            if fonte:
                novas_fontes += 1

                # Descobre sitemap e RSS
                urls_sitemap = await descobrir_sitemap(url)
                urls_rss = await descobrir_rss(url)

                for u in urls_sitemap[:100] + urls_rss[:50]:
                    await _adicionar_url_para_coleta(u, fonte.id, db)

        except Exception as e:
            logger.error(f"Erro ao cadastrar fonte {url}: {e}")

    logger.info(f"Ciclo descoberta concluído: {novas_fontes} novas fontes")
    return novas_fontes


async def expandir_fonte(fonte_id: int, db: AsyncSession) -> int:
    """
    Faz crawl de links dentro de uma fonte para descobrir mais páginas.
    Retorna número de novas URLs adicionadas à fila.
    """
    result = await db.execute(select(Fonte).where(Fonte.id == fonte_id))
    fonte = result.scalar_one_or_none()

    if not fonte:
        return 0

    resultado = await fetch_url(fonte.url, timeout=20)
    if not resultado:
        return 0

    html, _, url_final = resultado
    links = extrair_links(html, url_final)

    novos = 0
    for link in links:
        parsed = urlparse(link)
        dominio_link = parsed.netloc.lower().replace("www.", "")
        dominio_fonte = urlparse(fonte.url).netloc.lower().replace("www.", "")

        # Mantém links do mesmo domínio
        if dominio_link == dominio_fonte:
            adicionado = await _adicionar_url_para_coleta(link, fonte.id, db)
            if adicionado:
                novos += 1

    logger.info(f"Expandida fonte {fonte.dominio}: {novos} novas URLs")
    return novos


async def _adicionar_url_para_coleta(url: str, fonte_id: int, db: AsyncSession) -> bool:
    """Adiciona URL à fila de coleta se ainda não coletada."""
    from app.models import Conteudo
    from app.processing.deduplication import gerar_fingerprint_url

    url = gerar_fingerprint_url(url)
    if not url:
        return False

    result = await db.execute(select(Conteudo).where(Conteudo.url == url))
    if result.scalar_one_or_none():
        return False

    conteudo = Conteudo(
        fonte_id=fonte_id,
        url=url,
        status=ConteudoStatus.COLETADO.value,
        data_coleta=datetime.utcnow(),
    )
    db.add(conteudo)
    return True


# Importação condicional para evitar ciclo
from app.models.conteudo import ConteudoStatus
