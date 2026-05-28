"""
Sistema de classificação automática de entidades.
Extrai e classifica espécies, ingredientes, técnicas, equipamentos, locais e eventos
a partir do texto coletado. Aprende novos termos durante as coletas.
"""

import re
from collections import defaultdict
from unidecode import unidecode
from loguru import logger
from app.classifier.keywords import (
    ESPECIES, INGREDIENTES, AROMAS, TECNICAS, EQUIPAMENTOS, LOCAIS, EVENTOS,
    TERMOS_RELEVANCIA, TERMOS_EXCLUSAO
)


def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.lower()
    texto = unidecode(texto)
    texto = re.sub(r"[^\w\s-]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def calcular_score_relevancia(titulo: str, texto: str) -> float:
    """Calcula score de relevância 0-10 baseado em termos de pesca."""
    conteudo = f"{titulo or ''} {texto or ''}".lower()
    score = 0.0

    for termo in TERMOS_RELEVANCIA:
        if termo in conteudo:
            score += 1.0
            # Bonus se no título
            if titulo and termo in titulo.lower():
                score += 0.5

    for termo in TERMOS_EXCLUSAO:
        if termo in conteudo:
            score -= 3.0

    return max(0.0, min(10.0, score))


def extrair_entidades(titulo: str, texto: str) -> dict[str, list[dict]]:
    """
    Extrai todas as entidades do texto e retorna agrupadas por tipo.
    Retorna: {tipo: [{nome, frequencia, contexto}]}
    """
    conteudo_completo = f"{titulo or ''} {texto or ''}"
    conteudo_norm = normalizar_texto(conteudo_completo)

    resultados = defaultdict(dict)

    mapeamentos = [
        ("especie", ESPECIES),
        ("ingrediente", INGREDIENTES),
        ("aroma", AROMAS),
        ("tecnica", TECNICAS),
        ("equipamento", EQUIPAMENTOS),
        ("local", LOCAIS),
        ("evento", EVENTOS),
    ]

    for tipo, termos in mapeamentos:
        for termo in termos:
            termo_norm = normalizar_texto(termo)
            if not termo_norm:
                continue

            padrao = r"\b" + re.escape(termo_norm) + r"\b"
            matches = re.findall(padrao, conteudo_norm)

            if matches:
                freq = len(matches)
                # Extrai contexto (50 chars antes e depois)
                match = re.search(padrao, conteudo_norm)
                inicio = max(0, match.start() - 50)
                fim = min(len(conteudo_norm), match.end() + 50)
                contexto = conteudo_norm[inicio:fim]

                chave = termo_norm
                if chave not in resultados[tipo]:
                    resultados[tipo][chave] = {
                        "nome": termo,
                        "nome_normalizado": termo_norm,
                        "frequencia": freq,
                        "contexto": contexto,
                        "score_confianca": min(1.0, 0.7 + freq * 0.1),
                    }
                else:
                    resultados[tipo][chave]["frequencia"] += freq

    # Converte para lista
    resultado_final = {}
    for tipo, entidades in resultados.items():
        resultado_final[tipo] = list(entidades.values())

    return resultado_final


def classificar_categoria_conteudo(titulo: str, texto: str) -> str:
    """Classifica o conteúdo em uma categoria principal."""
    texto_completo = f"{titulo or ''} {texto or ''}".lower()

    regras = [
        ("receita_isca", ["receita", "ingrediente", "massa", "preparo", "como fazer", "mistura"]),
        ("tecnica_pesca", ["técnica", "montagem", "rig", "como pescar", "método", "estratégia"]),
        ("relato_captura", ["capturei", "peguei", "fisgou", "captura", "pesquei", "catch"]),
        ("review_produto", ["review", "avaliação", "testei", "unboxing", "produto", "equipamento"]),
        ("noticias", ["notícia", "campeonato", "torneio", "resultado", "vencedor"]),
        ("dica_pesca", ["dica", "truque", "segredo", "melhor horário", "como", "conselho"]),
        ("especie_peixe", ["espécie", "biologia", "características", "habitat", "alimentação do peixe"]),
        ("pesqueiro", ["pesqueiro", "lago", "pesque-pague", "valor", "preço", "estrutura"]),
    ]

    for categoria, termos in regras:
        for termo in termos:
            if termo in texto_completo:
                return categoria

    return "geral"


def detectar_novos_termos(texto: str, termos_existentes: set[str]) -> list[str]:
    """
    Detecta possíveis novos termos de pesca não presentes no dicionário.
    Usa heurísticas simples para identificar candidatos.
    """
    texto_norm = normalizar_texto(texto)
    novos_candidatos = []

    # Palavras após "pesca de", "técnica", "isca", "ingrediente"
    padroes = [
        r"pesca de (\w+(?:\s+\w+)?)",
        r"isca de (\w+(?:\s+\w+)?)",
        r"iscas? (\w+(?:\s+\w+)?)",
        r"tecnica (?:de\s+)?(\w+(?:\s+\w+)?)",
        r"ingrediente[:\s]+(\w+(?:\s+\w+)?)",
        r"aroma de (\w+(?:\s+\w+)?)",
    ]

    for padrao in padroes:
        matches = re.findall(padrao, texto_norm)
        for match in matches:
            match = match.strip()
            if match and match not in termos_existentes and len(match) > 3:
                novos_candidatos.append(match)

    return list(set(novos_candidatos))


# Cache de todos os termos normalizados para uso no score de relevância
_TODOS_TERMOS = set()
for _lista in [ESPECIES, INGREDIENTES, AROMAS, TECNICAS, EQUIPAMENTOS, LOCAIS, EVENTOS]:
    for _t in _lista:
        _TODOS_TERMOS.add(normalizar_texto(_t))
