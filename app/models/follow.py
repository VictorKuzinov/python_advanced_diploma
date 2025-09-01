# Стандартная библиотека
from datetime import datetime

# Сторонние пакеты
from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Локальные
from app.db.base import Base


class Follow(Base):
    """
    Подписка: кто на кого подписан.
    follower_id — кто подписался (читатель),
    followee_id — на кого подписался (автор).
    """
    __tablename__ = "follows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    follower_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    followee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("follower_id", "followee_id", name="uq_follow_pair"),
    )

    # связи
    # пользователь, который подписался (читатель)
    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")

    # пользователь, на которого подписались (автор / тот которого читают)
    followee = relationship("User", foreign_keys=[followee_id], back_populates="followers")
