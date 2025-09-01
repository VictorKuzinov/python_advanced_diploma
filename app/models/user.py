# Стандартная библиотека
# (здесь ничего не нужно)

# Сторонние пакеты
# Сторонние пакеты
from sqlalchemy import DateTime, func, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Локальные
from app.db.base import Base


class User(Base):
    """
    Модель Пользователь:
    хранит username и api_key для авторизации.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    api_key: Mapped[str]   = mapped_column(String(100), nullable=False, unique=True, index=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Связи:
    # один пользователь много твитов
    tweets = relationship("Tweet", back_populates="author", cascade="all, delete-orphan")

    # подписки (кого я читаю)
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan")

    # подписчики (кто меня читает)
    followers = relationship("Follow", foreign_keys="Follow.followee_id", back_populates="followee", cascade="all, delete-orphan")

    # лайки пользователя
    likes =  relationship("Like", back_populates="user", cascade="all, delete-orphan")
