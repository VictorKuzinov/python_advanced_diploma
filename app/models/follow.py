# app/models/follow.py
from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    followee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # ВАЖНО: уникальная пара, чтобы не было дублей подписок
    __table_args__ = (UniqueConstraint("follower_id", "followee_id", name="uq_follow_pair"),)

    follower = relationship("User", foreign_keys=[follower_id])
    followee = relationship("User", foreign_keys=[followee_id])
