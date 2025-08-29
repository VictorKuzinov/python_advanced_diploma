# Стандартная библиотека
# (здесь ничего не нужно)

# Сторонние пакеты
from sqlalchemy import DateTime, ForeignKey, func, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Локальные
from app.db.base import Base


class Tweet(Base):
    """
    Модель твита:
    хранит автора и контент
    """

    __tablename__ = "tweets"

    # Модель:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(String(280), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Связи:
    # Один пользователь → много твитов
    author = relationship("User", back_populates="tweets")

    # Твит имеет много лайков
    likes = relationship("Like", back_populates="tweet", cascade="all, delete-orphan")

    # Твит имеет много вложений (Media)
    attachments = relationship("Media", secondary="tweet_media", back_populates="tweets", lazy="selectin")
