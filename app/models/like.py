# Стандартная библиотека
from datetime import datetime

# Сторонние пакеты
from sqlalchemy import DateTime, ForeignKey, func, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Локальные
from app.db.base import Base


class Like(Base):
    """
    Модель лайка: связь пользователь → твит.
    Один пользователь не может лайкнуть один и тот же твит дважды.
    """
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),  # если пользователь удалён — его лайки удаляются
        nullable=False,
        index=True,
    )

    tweet_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tweets.id", ondelete="CASCADE"),  # если твит удалён — лайки на него удаляются
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "tweet_id", name="uq_user_tweet"),  # уникальная пара (user, tweet)
    )

    # связи:
    # какой пользователь поставил лайк
    user = relationship(
        "User",
        back_populates="likes"
    )

    # какой твит был лайкнут
    tweet = relationship(
        "Tweet",
        back_populates="likes"
    )
