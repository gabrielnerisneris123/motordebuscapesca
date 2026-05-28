import enum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class TipoLog(str, enum.Enum):
    INFO = "info"
    ERRO = "erro"
    AVISO = "aviso"
    DUPLICADO = "duplicado"
    DESCOBERTA = "descoberta"
    COLETA = "coleta"
    PROCESSAMENTO = "processamento"


class LogColeta(Base):
    __tablename__ = "logs_coleta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    fonte_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fontes.id", ondelete="SET NULL"), index=True
    )
    conteudo_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("conteudos.id", ondelete="SET NULL"), index=True
    )
    url: Mapped[str | None] = mapped_column(String(2048))
    dados_extras: Mapped[dict | None] = mapped_column(JSON)
    data_hora: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    worker: Mapped[str | None] = mapped_column(String(128))

    __table_args__ = (
        Index("idx_logs_tipo_data", "tipo", "data_hora"),
    )

    def __repr__(self) -> str:
        return f"<Log {self.tipo}: {self.mensagem[:50]}>"
