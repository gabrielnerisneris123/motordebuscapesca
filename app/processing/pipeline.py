"""
Pipeline de processamento completo: limpeza → deduplicação → classificação → armazenamento.
"""

from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.processing.cleaner import limpar_html, extrair_metadados, extrair_links
from app.processing.deduplication import gerar_hash_conteudo, gerar_simhash
from app.classifier.entities import (
    extrair_entidades, calcular_score_relevancia, classificar_categoria_conteudo
)
from app.models import Conteudo, ConteudoStatus, Entidade, ConteudoEntidade, TipoEntidade


async def processar_conteudo(
    conteudo_id: int,
    db: AsyncSession,
) -> bool:
    """
    Processa um conteúdo coletado: limpa, classifica e extrai entidades.
    Retorna True se processado com sucesso.
    """
    result = await db.execute(select(Conteudo).where(Conteudo.id == conteudo_id))
    conteudo = result.scalar_one_or_none()

    if not conteudo:
        logger.warning(f"Conteúdo {conteudo_id} não encontrado")
        return False

    if not conteudo.conteudo_html:
        conteudo.status = ConteudoStatus.ERRO.value
        conteudo.erro_msg = "HTML vazio"
        return False

    try:
        # Limpeza
        titulo, texto = limpar_html(conteudo.conteudo_html)
        metadados = extrair_metadados(conteudo.conteudo_html, conteudo.url)

        if titulo and not conteudo.titulo:
            conteudo.titulo = titulo[:1024]

        conteudo.conteudo_texto = texto
        conteudo.num_palavras = len(texto.split()) if texto else 0
        conteudo.tamanho_bytes = len(texto.encode("utf-8")) if texto else 0

        # Atualiza metadados
        if not conteudo.autor and metadados.get("autor"):
            conteudo.autor = metadados["autor"][:512]

        if metadados.get("tags"):
            conteudo.tags = metadados["tags"]

        if metadados.get("imagens"):
            conteudo.imagens = metadados["imagens"]

        # Hash para deduplicação
        conteudo.hash_conteudo = gerar_hash_conteudo(texto)
        conteudo.hash_simhash = gerar_simhash(texto)

        # Score de relevância
        conteudo.score_relevancia = calcular_score_relevancia(titulo, texto)

        # Classifica categoria
        categoria = classificar_categoria_conteudo(titulo, texto)
        if not conteudo.categorias:
            conteudo.categorias = [categoria]

        # Extrai e persiste entidades
        if texto and conteudo.score_relevancia > 0:
            entidades = extrair_entidades(titulo, texto)
            await _persistir_entidades(conteudo.id, entidades, db)

        conteudo.status = ConteudoStatus.PROCESSADO.value
        conteudo.data_processamento = datetime.utcnow()

        logger.info(
            f"Processado: {conteudo.url[:60]} | "
            f"score={conteudo.score_relevancia:.1f} | "
            f"palavras={conteudo.num_palavras}"
        )
        return True

    except Exception as e:
        logger.error(f"Erro ao processar conteúdo {conteudo_id}: {e}")
        conteudo.status = ConteudoStatus.ERRO.value
        conteudo.erro_msg = str(e)[:500]
        return False


async def _persistir_entidades(
    conteudo_id: int,
    entidades: dict[str, list[dict]],
    db: AsyncSession,
) -> None:
    """Persiste entidades extraídas no banco, criando ou atualizando registros."""

    for tipo, lista in entidades.items():
        for item in lista:
            nome_norm = item["nome_normalizado"]

            # Busca ou cria entidade
            result = await db.execute(
                select(Entidade).where(
                    Entidade.tipo == tipo,
                    Entidade.nome_normalizado == nome_norm,
                )
            )
            entidade = result.scalar_one_or_none()

            if not entidade:
                entidade = Entidade(
                    nome=item["nome"],
                    nome_normalizado=nome_norm,
                    tipo=tipo,
                    frequencia=item["frequencia"],
                    score_confianca=item["score_confianca"],
                )
                db.add(entidade)
                await db.flush()
            else:
                entidade.frequencia += item["frequencia"]
                entidade.data_atualizacao = datetime.utcnow()

            # Cria relação conteudo-entidade se não existir
            result = await db.execute(
                select(ConteudoEntidade).where(
                    ConteudoEntidade.conteudo_id == conteudo_id,
                    ConteudoEntidade.entidade_id == entidade.id,
                )
            )
            relacao = result.scalar_one_or_none()

            if not relacao:
                relacao = ConteudoEntidade(
                    conteudo_id=conteudo_id,
                    entidade_id=entidade.id,
                    frequencia_no_texto=item["frequencia"],
                    contexto=item.get("contexto", "")[:500],
                    score_confianca=item["score_confianca"],
                )
                db.add(relacao)
            else:
                relacao.frequencia_no_texto += item["frequencia"]
