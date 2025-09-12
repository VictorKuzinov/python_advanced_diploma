# Стандартная библиотека
from datetime import datetime

# Сторонние пакеты
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# локальные пакеты
from app.db.base import Base

tweet_media = Table(
    "tweet_media",
    Base.metadata,
    Column(
        "tweet_id",
        Integer,
        ForeignKey("tweets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "media_id",
        Integer,
        ForeignKey("medias.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Media(Base):
    """
    Медиафайл:
    храним относительный путь (по ТЗ).
    """

    __tablename__ = "medias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tweets = relationship("Tweet", secondary="tweet_media", back_populates="attachments")
