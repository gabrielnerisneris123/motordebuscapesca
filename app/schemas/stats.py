from pydantic import BaseModel
from typing import Optional


class EstatisticasGerais(BaseModel):
    total_fontes: int
    fontes_ativas: int
    total_conteudos: int
    conteudos_processados: int
    conteudos_duplicados: int
    total_entidades: int
    total_palavras: int
    fontes_por_status: dict
    conteudos_por_status: dict


class EstatisticasColeta(BaseModel):
    fonte_id: int
    dominio: str
    paginas_coletadas: int
    ultima_coleta: Optional[str]
    status: str
    score_relevancia: float


class EntidadeFrequencia(BaseModel):
    id: int
    nome: str
    tipo: str
    frequencia: int
    score_confianca: float

    model_config = {"from_attributes": True}


class LogItem(BaseModel):
    id: int
    tipo: str
    mensagem: str
    url: Optional[str]
    data_hora: str
    worker: Optional[str]

    model_config = {"from_attributes": True}
