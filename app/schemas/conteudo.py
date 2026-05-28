from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class ConteudoRead(BaseModel):
    id: int
    fonte_id: int
    url: str
    titulo: Optional[str]
    resumo: Optional[str]
    autor: Optional[str]
    categorias: Optional[list]
    tags: Optional[list]
    data_publicacao: Optional[datetime]
    data_coleta: datetime
    status: str
    num_palavras: int
    score_relevancia: float
    idioma: Optional[str]

    model_config = {"from_attributes": True}


class ConteudoDetalhe(ConteudoRead):
    conteudo_texto: Optional[str]
    metadados: Optional[dict]
    imagens: Optional[list]


class ConteudoList(BaseModel):
    items: list[ConteudoRead]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int


class ConteudoFiltro(BaseModel):
    fonte_id: Optional[int] = None
    status: Optional[str] = None
    busca: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    score_min: Optional[float] = None
    pagina: int = 1
    por_pagina: int = 50
