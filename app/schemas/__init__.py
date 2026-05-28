from app.schemas.fonte import FonteCreate, FonteRead, FonteList, FonteUpdate
from app.schemas.conteudo import ConteudoRead, ConteudoList, ConteudoFiltro
from app.schemas.stats import EstatisticasGerais, EstatisticasColeta

__all__ = [
    "FonteCreate", "FonteRead", "FonteList", "FonteUpdate",
    "ConteudoRead", "ConteudoList", "ConteudoFiltro",
    "EstatisticasGerais", "EstatisticasColeta",
]
