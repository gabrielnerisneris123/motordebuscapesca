import enum
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Enum, Boolean, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class FonteStatus(str, enum.Enum):
    PENDENTE = "pendente"
    ATIVA = "ativa"
    ERRO = "erro"
    BLOQUEADA = "bloqueada"
    INATIVA = "inativa"


class FonteCategoria(str, enum.Enum):
    BLOG = "blog"
    FORUM = "forum"
    PORTAL = "portal"
    REVISTA = "revista"
    LOJA = "loja"
    PESQUEIRO = "pesqueiro"
    FABRICANTE = "fabricante"
    NOTICIAS = "noticias"
    YOUTUBE = "youtube"
    OUTRO = "outro"


class Fonte(Base):
    __tablename__ = "fontes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
    dominio: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    nome: Mapped[str | None] = mapped_column(String(512))
    descricao: Mapped[str | None] = mapped_column(Text)
    categoria: Mapped[str] = mapped_column(
        String(50), default=FonteCategoria.OUTRO.value, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=FonteStatus.PENDENTE.value, index=True
    )
    score_relevancia: Mapped[float] = mapped_column(Float, default=0.0)
    total_paginas: Mapped[int] = mapped_column(Integer, default=0)
    paginas_coletadas: Mapped[int] = mapped_column(Integer, default=0)
    ultima_coleta: Mapped[datetime | None] = mapped_column(DateTime)
    proxima_coleta: Mapped[datetime | None] = mapped_column(DateTime)
    data_descoberta: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    tem_sitemap: Mapped[bool] = mapped_column(Boolean, default=False)
    tem_rss: Mapped[bool] = mapped_column(Boolean, default=False)
    url_sitemap: Mapped[str | None] = mapped_column(String(2048))
    url_rss: Mapped[str | None] = mapped_column(String(2048))
    requer_javascript: Mapped[bool] = mapped_column(Boolean, default=False)
    robots_txt: Mapped[str | None] = mapped_column(Text)
    erro_msg: Mapped[str | None] = mapped_column(Text)
    tentativas_erro: Mapped[int] = mapped_column(Integer, default=0)
    descoberta_via: Mapped[str | None] = mapped_column(String(256))

    conteudos: Mapped[list["Conteudo"]] = relationship(
        "Conteudo", back_populates="fonte", lazy="select"
    )

    __table_args__ = (
        Index("idx_fontes_status_proxima_coleta", "status", "proxima_coleta"),
        Index("idx_fontes_score", "score_relevancia"),
    )

    def __repr__(self) -> str:
        return f"<Fonte {self.dominio}>"
