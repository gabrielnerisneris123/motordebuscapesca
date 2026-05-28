"""
Pipeline de limpeza de HTML e normalização de texto.
Remove scripts, estilos, anúncios e elementos de navegação.
"""

import re
import ftfy
from bs4 import BeautifulSoup
from unidecode import unidecode
from loguru import logger


# Tags HTML a remover completamente (incluindo conteúdo)
TAGS_REMOVER = {
    "script", "style", "noscript", "iframe", "frame", "object",
    "embed", "applet", "form", "input", "button", "select",
    "textarea", "nav", "footer", "header", "aside", "menu",
    "advertisement", "ads", "banner",
}

# Classes/IDs que geralmente contêm anúncios ou navegação
CLASSES_REMOVER = {
    "nav", "navigation", "menu", "sidebar", "footer", "header",
    "advertisement", "ads", "ad", "banner", "cookie", "popup",
    "modal", "overlay", "newsletter", "social", "share", "related",
    "recommendation", "breadcrumb", "pagination", "comments-section",
    "widget", "plugin", "toolbar",
}

IDS_REMOVER = {
    "nav", "navigation", "menu", "sidebar", "footer", "header",
    "ad", "ads", "banner", "cookie-notice", "cookie-bar",
    "newsletter", "popup", "modal", "overlay",
}


def limpar_html(html: str) -> tuple[str, str]:
    """
    Limpa HTML e extrai título e texto limpo.
    Retorna: (titulo, texto_limpo)
    """
    if not html:
        return "", ""

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as e:
            logger.error(f"Erro ao parsear HTML: {e}")
            return "", ""

    # Extrai título
    titulo = ""
    tag_titulo = soup.find("title")
    if tag_titulo:
        titulo = tag_titulo.get_text(strip=True)

    # Tenta h1 se título estiver vazio ou genérico
    if not titulo or len(titulo) < 5:
        h1 = soup.find("h1")
        if h1:
            titulo = h1.get_text(strip=True)

    # Remove tags indesejadas
    for tag in TAGS_REMOVER:
        for elemento in soup.find_all(tag):
            elemento.decompose()

    # Remove por classe
    for classe in CLASSES_REMOVER:
        for elemento in soup.find_all(class_=re.compile(classe, re.I)):
            elemento.decompose()

    # Remove por ID
    for id_val in IDS_REMOVER:
        elemento = soup.find(id=re.compile(id_val, re.I))
        if elemento:
            elemento.decompose()

    # Remove comentários HTML
    from bs4 import Comment
    for comentario in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comentario.extract()

    # Tenta extrair conteúdo principal
    conteudo_principal = (
        soup.find("article")
        or soup.find("main")
        or soup.find(id=re.compile(r"content|post|article|entry", re.I))
        or soup.find(class_=re.compile(r"content|post|article|entry|text", re.I))
        or soup.find("body")
        or soup
    )

    # Extrai texto
    texto = conteudo_principal.get_text(separator="\n", strip=True)

    # Limpa o texto
    texto = _normalizar_texto(texto)

    return titulo, texto


def _normalizar_texto(texto: str) -> str:
    """Normaliza e limpa texto extraído."""
    if not texto:
        return ""

    # Corrige encoding com ftfy
    texto = ftfy.fix_text(texto)

    # Remove linhas com menos de 3 caracteres
    linhas = [l.strip() for l in texto.split("\n") if len(l.strip()) >= 3]

    # Remove linhas duplicadas consecutivas
    linhas_unicas = []
    anterior = None
    for linha in linhas:
        if linha != anterior:
            linhas_unicas.append(linha)
        anterior = linha

    texto = "\n".join(linhas_unicas)

    # Normaliza espaços
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()


def extrair_metadados(html: str, url: str) -> dict:
    """Extrai metadados Open Graph, meta tags e outros."""
    if not html:
        return {}

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return {}

    meta = {}

    # Open Graph
    for tag in soup.find_all("meta", property=re.compile(r"^og:", re.I)):
        prop = tag.get("property", "").replace("og:", "")
        content = tag.get("content", "")
        if prop and content:
            meta[f"og_{prop}"] = content

    # Meta description e keywords
    desc = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if desc:
        meta["description"] = desc.get("content", "")

    keywords = soup.find("meta", attrs={"name": re.compile(r"keywords", re.I)})
    if keywords:
        meta["keywords"] = keywords.get("content", "")

    # Autor
    autor = (
        soup.find("meta", attrs={"name": re.compile(r"author", re.I)})
        or soup.find(class_=re.compile(r"author|autor", re.I))
    )
    if autor:
        meta["autor"] = autor.get("content", "") or autor.get_text(strip=True)

    # Data de publicação
    for seletor in [
        {"name": re.compile(r"date|published", re.I)},
        {"property": re.compile(r"published_time|date", re.I)},
    ]:
        tag_data = soup.find("meta", attrs=seletor)
        if tag_data:
            meta["data_publicacao"] = tag_data.get("content", "")
            break

    # Extrai imagens
    imagens = []
    for img in soup.find_all("img", src=True)[:20]:
        src = img.get("src", "")
        alt = img.get("alt", "")
        if src and not src.startswith("data:"):
            imagens.append({"src": src, "alt": alt})
    meta["imagens"] = imagens

    # Extrai tags/categorias
    tags = []
    for tag in soup.find_all(class_=re.compile(r"tag|categoria|label", re.I)):
        texto = tag.get_text(strip=True)
        if texto and len(texto) < 100:
            tags.append(texto)
    meta["tags"] = list(set(tags))[:20]

    return meta


def extrair_links(html: str, url_base: str) -> list[str]:
    """Extrai todos os links de uma página."""
    if not html:
        return []

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return []

    from urllib.parse import urljoin, urlparse

    links = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        url_absoluta = urljoin(url_base, href)
        parsed = urlparse(url_absoluta)

        if parsed.scheme in ("http", "https"):
            # Remove fragmento
            url_limpa = url_absoluta.split("#")[0].rstrip("/")
            links.add(url_limpa)

    return list(links)
