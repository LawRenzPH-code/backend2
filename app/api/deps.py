# app/api/deps.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.config import settings
from app.crud.crud_user import user_crud
from app.schemas.user import TokenData
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token"
)

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
        
    user = user_crud.get_by_email(db, email=token_data.username)
    if user is None:
        raise credentials_exception
    if not user_crud.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user

def get_optional_current_user(
    db: Session = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    if token is None:
        return None
    try:
        return get_current_user(db, token)
    except HTTPException:
        return None