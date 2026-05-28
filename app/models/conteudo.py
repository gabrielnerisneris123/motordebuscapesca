import enum
from datetime import datetime
from sqlalchemy import (
    String, Integer, DateTime, Text, ForeignKey,
    Index, Boolean, Float, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ConteudoStatus(str, enum.Enum):
    COLETADO = "coletado"
    PROCESSADO = "processado"
    DUPLICADO = "duplicado"
    ERRO = "erro"


class Conteudo(Base):
    __tablename__ = "conteudos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fonte_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fontes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
    url_canonica: Mapped[str | None] = mapped_column(String(2048))
    titulo: Mapped[str | None] = mapped_column(String(1024))
    conteudo_html: Mapped[str | None] = mapped_column(Text)
    conteudo_texto: Mapped[str | None] = mapped_column(Text)
    resumo: Mapped[str | None] = mapped_column(Text)
    autor: Mapped[str | None] = mapped_column(String(512))
    categorias: Mapped[list | None] = mapped_column(JSON)
    tags: Mapped[list | None] = mapped_column(JSON)
    imagens: Mapped[list | None] = mapped_column(JSON)
    comentarios: Mapped[list | None] = mapped_column(JSON)
    data_publicacao: Mapped[datetime | None] = mapped_column(DateTime)
    data_coleta: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    data_processamento: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(
        String(20), default=ConteudoStatus.COLETADO.value, index=True
    )
    hash_conteudo: Mapped[str | None] = mapped_column(String(64), index=True)
    hash_simhash: Mapped[str | None] = mapped_column(String(64))
    tamanho_bytes: Mapped[int] = mapped_column(Integer, default=0)
    num_palavras: Mapped[int] = mapped_column(Integer, default=0)
    score_relevancia: Mapped[float] = mapped_column(Float, default=0.0)
    idioma: Mapped[str | None] = mapped_column(String(10))
    erro_msg: Mapped[str | None] = mapped_column(Text)
    metadados: Mapped[dict | None] = mapped_column(JSON)

    fonte: Mapped["Fonte"] = relationship("Fonte", back_populates="conteudos")
    entidades: Mapped[list["ConteudoEntidade"]] = relationship(
        "ConteudoEntidade", back_populates="conteudo", lazy="select"
    )

    __table_args__ = (
        Index("idx_conteudos_data_coleta", "data_coleta"),
        Index("idx_conteudos_data_publicacao", "data_publicacao"),
        Index("idx_conteudos_hash", "hash_conteudo"),
        Index("idx_conteudos_status_fonte", "status", "fonte_id"),
    )

    def __repr__(self) -> str:
        return f"<Conteudo {self.url[:60]}>"
