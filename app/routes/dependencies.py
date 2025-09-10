# app/routes/dependencies.py
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services import users as user_service
from app.models import User

async def get_current_user(
    api_key: str = Header(..., alias="api-key"),
    session: AsyncSession = Depends(get_session),
) -> User:
    user = await user_service._get_user_by_api_key(session, api_key=api_key)
    if not user:
        # семантика та же, что и раньше через EntityNotFound → 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing api-key",
        )
    return user