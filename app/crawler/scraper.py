"""
Motor de scraping: combina requests simples com Playwright para sites dinâmicos.
"""

import asyncio
from datetime import datetime
from urllib.parse import urlparse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crawler.http_client import fetch_url
from app.processing.cleaner import limpar_html, extrair_metadados, extrair_links
from app.processing.deduplication import gerar_hash_conteudo, gerar_simhash, gerar_fingerprint_url
from app.models import Conteudo, ConteudoStatus, Fonte, FonteStatus
from app.config import settings


async def coletar_url_simples(url: str) -> dict | None:
    """
    Coleta uma URL usando requests simples (sem JavaScript).
    Retorna dicionário com dados coletados ou None.
    """
    resultado = await fetch_url(url)
    if not resultado:
        return None

    html, status, url_final = resultado

    if not html or len(html) < 200:
        return None

    titulo, texto = limpar_html(html)
    meta = extrair_metadados(html, url_final)
    links = extrair_links(html, url_final)

    return {
        "url": url_final,
        "html": html,
        "titulo": titulo,
        "texto": texto,
        "meta": meta,
        "links": links,
        "metodo": "simples",
    }


async def coletar_url_playwright(url: str) -> dict | None:
    """
    Coleta uma URL usando Playwright (suporta JavaScript).
    Usado para sites que carregam conteúdo dinamicamente.
    """
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.playwright_headless,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = await browser.new_context(
                locale="pt-BR",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1280, "height": 720},
            )

            page = await context.new_page()

            # Bloqueia recursos desnecessários
            await page.route(
                "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,mp4,mp3}",
                lambda route: route.abort(),
            )
            await page.route(
                "**/analytics*|**/gtag*|**/facebook*|**/doubleclick*",
                lambda route: route.abort(),
            )

            try:
                await page.goto(url, timeout=settings.playwright_timeout, wait_until="domcontentloaded")
                await asyncio.sleep(2)

                html = await page.content()
                url_final = page.url

            except Exception as e:
                logger.warning(f"Playwright erro para {url}: {e}")
                return None
            finally:
                await browser.close()

        if not html:
            return None

        titulo, texto = limpar_html(html)
        meta = extrair_metadados(html, url_final)
        links = extrair_links(html, url_final)

        return {
            "url": url_final,
            "html": html,
            "titulo": titulo,
            "texto": texto,
            "meta": meta,
            "links": links,
            "metodo": "playwright",
        }

    except Exception as e:
        logger.error(f"Erro Playwright para {url}: {e}")
        return None


async def coletar_e_salvar(
    conteudo_id: int,
    db: AsyncSession,
    forcar_playwright: bool = False,
) -> bool:
    """
    Coleta uma URL e salva no banco.
    Retorna True se coletado com sucesso.
    """
    result = await db.execute(
        select(Conteudo).where(Conteudo.id == conteudo_id)
    )
    conteudo = result.scalar_one_or_none()

    if not conteudo:
        return False

    # Verifica se a fonte requer JavaScript
    result_fonte = await db.execute(
        select(Fonte).where(Fonte.id == conteudo.fonte_id)
    )
    fonte = result_fonte.scalar_one_or_none()
    usar_playwright = forcar_playwright or (fonte and fonte.requer_javascript)

    # Coleta
    dados = None
    try:
        if usar_playwright:
            dados = await coletar_url_playwright(conteudo.url)
        else:
            dados = await coletar_url_simples(conteudo.url)
            # Se falhou ou parece dinâmico, tenta com Playwright
            if not dados and fonte:
                logger.info(f"Tentando Playwright para {conteudo.url}")
                dados = await coletar_url_playwright(conteudo.url)
                if dados and fonte:
                    fonte.requer_javascript = True

    except Exception as e:
        logger.error(f"Erro ao coletar {conteudo.url}: {e}")
        conteudo.status = ConteudoStatus.ERRO.value
        conteudo.erro_msg = str(e)[:500]
        return False

    if not dados:
        conteudo.status = ConteudoStatus.ERRO.value
        conteudo.erro_msg = "Sem conteúdo retornado"
        if fonte:
            fonte.tentativas_erro += 1
        return False

    # Verifica duplicidade por hash
    texto = dados.get("texto", "")
    hash_conteudo = gerar_hash_conteudo(texto)

    if hash_conteudo:
        result = await db.execute(
            select(Conteudo).where(
                Conteudo.hash_conteudo == hash_conteudo,
                Conteudo.id != conteudo_id,
            )
        )
        duplicado = result.scalar_one_or_none()
        if duplicado:
            conteudo.status = ConteudoStatus.DUPLICADO.value
            conteudo.hash_conteudo = hash_conteudo
            logger.debug(f"Duplicado detectado: {conteudo.url}")
            if fonte:
                fonte.paginas_coletadas += 1
            return True

    # Salva dados
    conteudo.conteudo_html = dados.get("html", "")[:10_000_000]  # 10MB max
    conteudo.conteudo_texto = texto
    conteudo.titulo = (dados.get("titulo", "") or "")[:1024]
    conteudo.hash_conteudo = hash_conteudo
    conteudo.hash_simhash = gerar_simhash(texto)
    conteudo.num_palavras = len(texto.split()) if texto else 0
    conteudo.tamanho_bytes = len(texto.encode("utf-8")) if texto else 0
    conteudo.data_coleta = datetime.utcnow()

    meta = dados.get("meta", {})
    if meta.get("autor"):
        conteudo.autor = str(meta["autor"])[:512]
    if meta.get("tags"):
        conteudo.tags = meta["tags"]
    if meta.get("imagens"):
        conteudo.imagens = meta["imagens"]

    # Tenta extrair data de publicação
    data_pub = meta.get("data_publicacao") or meta.get("og_article:published_time")
    if data_pub:
        from app.crawler.utils import parsear_data
        conteudo.data_publicacao = parsear_data(data_pub)

    conteudo.status = ConteudoStatus.PROCESSADO.value
    conteudo.metadados = {k: v for k, v in meta.items() if k not in ("imagens", "tags")}

    # Atualiza fonte
    if fonte:
        fonte.paginas_coletadas += 1
        fonte.ultima_coleta = datetime.utcnow()
        fonte.tentativas_erro = 0

    # Descobre novos links para coletar
    links = dados.get("links", [])
    if fonte and links:
        await _enfileirar_links(links, fonte, db)

    logger.info(f"Coletado: {conteudo.url[:60]} | palavras={conteudo.num_palavras}")
    return True


async def _enfileirar_links(links: list[str], fonte: Fonte, db: AsyncSession) -> int:
    """Enfileira novos links do mesmo domínio para coleta."""
    from app.processing.deduplication import gerar_fingerprint_url

    dominio_fonte = urlparse(fonte.url).netloc.lower().replace("www.", "")
    novos = 0

    # Limita para não sobrecarregar
    limite = min(len(links), 50)

    for link in links[:limite]:
        try:
            link_norm = gerar_fingerprint_url(link)
            if not link_norm:
                continue

            parsed = urlparse(link_norm)
            dominio_link = parsed.netloc.lower().replace("www.", "")

            # Só enfileira links do mesmo domínio
            if dominio_link != dominio_fonte:
                continue

            result = await db.execute(
                select(Conteudo).where(Conteudo.url == link_norm)
            )
            if not result.scalar_one_or_none():
                novo = Conteudo(
                    fonte_id=fonte.id,
                    url=link_norm,
                    status="pendente",
                    data_coleta=datetime.utcnow(),
                )
                db.add(novo)
                novos += 1

        except Exception:
            pass

    return novos


async def coletar_lote(
    fonte_id: int,
    db: AsyncSession,
    limite: int = None,
) -> dict:
    """
    Coleta um lote de URLs pendentes de uma fonte.
    Retorna estatísticas do lote.
    """
    limite = limite or settings.batch_size

    result = await db.execute(
        select(Conteudo)
        .where(
            Conteudo.fonte_id == fonte_id,
            Conteudo.status.in_(["pendente", ConteudoStatus.COLETADO.value]),
        )
        .limit(limite)
    )
    conteudos = result.scalars().all()

    stats = {"total": len(conteudos), "sucesso": 0, "erro": 0, "duplicado": 0}

    semaphore = asyncio.Semaphore(settings.max_concurrent_requests // 2)

    async def coletar_com_semaphore(c):
        async with semaphore:
            return await coletar_e_salvar(c.id, db)

    resultados = await asyncio.gather(
        *[coletar_com_semaphore(c) for c in conteudos],
        return_exceptions=True,
    )

    for r in resultados:
        if isinstance(r, Exception):
            stats["erro"] += 1
        elif r:
            stats["sucesso"] += 1
        else:
            stats["erro"] += 1

    await db.commit()

    logger.info(f"Lote fonte {fonte_id}: {stats}")
    return stats
