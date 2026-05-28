import enum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Index, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TipoEntidade(str, enum.Enum):
    ESPECIE = "especie"
    INGREDIENTE = "ingrediente"
    TECNICA = "tecnica"
    EQUIPAMENTO = "equipamento"
    LOCAL = "local"
    EVENTO = "evento"
    ISCA = "isca"
    AROMA = "aroma"
    ADITIVO = "aditivo"
    RACAO = "racao"
    RECEITA = "receita"
    OUTRO = "outro"


class Entidade(Base):
    __tablename__ = "entidades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(512), nullable=False)
    nome_normalizado: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    aliases: Mapped[list | None] = mapped_column(JSON)
    descricao: Mapped[str | None] = mapped_column(Text)
    nome_cientifico: Mapped[str | None] = mapped_column(String(512))
    dados_extras: Mapped[dict | None] = mapped_column(JSON)
    frequencia: Mapped[int] = mapped_column(Integer, default=1)
    score_confianca: Mapped[float] = mapped_column(Float, default=1.0)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    data_atualizacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conteudos: Mapped[list["ConteudoEntidade"]] = relationship(
        "ConteudoEntidade", back_populates="entidade", lazy="select"
    )

    __table_args__ = (
        Index("idx_entidades_tipo_nome", "tipo", "nome_normalizado", unique=True),
        Index("idx_entidades_frequencia", "frequencia"),
    )

    def __repr__(self) -> str:
        return f"<Entidade {self.tipo}:{self.nome}>"


class ConteudoEntidade(Base):
    __tablename__ = "conteudo_entidades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conteudo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conteudos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entidade_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    frequencia_no_texto: Mapped[int] = mapped_column(Integer, default=1)
    contexto: Mapped[str | None] = mapped_column(Text)
    score_confianca: Mapped[float] = mapped_column(Float, default=1.0)

    conteudo: Mapped["Conteudo"] = relationship("Conteudo", back_populates="entidades")
    entidade: Mapped["Entidade"] = relationship("Entidade", back_populates="conteudos")

    __table_args__ = (
        Index("idx_ce_conteudo_entidade", "conteudo_id", "entidade_id", unique=True),
    )
