from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from app.models.fonte import FonteStatus, FonteCategoria


class FonteCreate(BaseModel):
    url: str
    nome: Optional[str] = None
    categoria: str = FonteCategoria.OUTRO.value

    @field_validator("url")
    @classmethod
    def validar_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        return v.strip()


class FonteUpdate(BaseModel):
    nome: Optional[str] = None
    categoria: Optional[str] = None
    status: Optional[str] = None
    score_relevancia: Optional[float] = None


class FonteRead(BaseModel):
    id: int
    url: str
    dominio: str
    nome: Optional[str]
    descricao: Optional[str]
    categoria: str
    status: str
    score_relevancia: float
    total_paginas: int
    paginas_coletadas: int
    ultima_coleta: Optional[datetime]
    data_descoberta: datetime
    tem_sitemap: bool
    tem_rss: bool
    descoberta_via: Optional[str]

    model_config = {"from_attributes": True}


class FonteList(BaseModel):
    items: list[FonteRead]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int
