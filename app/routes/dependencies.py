# app/routes/dependencies.py
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import User
from app.services import users as user_service


async def get_current_user(
    api_key: Optional[str] = Header(None, alias="api-key"),
    session: AsyncSession = Depends(get_session),
) -> User:
    # 1) Нет заголовка → 401 (и не зовём сервис вовсе)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing api-key",
        )

    # 2) Есть заголовок, проверяем пользователя
    user = await user_service._get_user_by_api_key(session, api_key=api_key)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid api-key",
        )

    return user
