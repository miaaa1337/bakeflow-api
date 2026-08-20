from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import APIKeyHeader
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import models
from database import get_db  # Берем единую асинхронную get_db из database.py
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def hash_pin(pin: str) -> str:
    return pwd_context.hash(pin)


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    return pwd_context.verify(plain_pin, hashed_pin)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


oauth2_scheme = APIKeyHeader(name="Authorization", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
  credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Авторизация не выполнена",
      headers={"WWW-Authenticate": "Bearer"},
  )

  if not token:
    raise credentials_exception

  if token.startswith("Bearer "):
    token = token.split(" ", 1)[1]

  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    employee_id_raw = payload.get("sub")
    if employee_id_raw is None:
      raise credentials_exception
    employee_id = int(employee_id_raw)
  except Exception as e:
    # 🛑 ВЫВЕДЕМ РЕАЛЬНУЮ ПРИЧИНУ ПАДЕНИЯ В КОНСОЛЬ!
    print(f"\n🔥🔥 РЕАЛЬНАЯ ОШИБКА В GET_CURRENT_USER: {repr(e)}")
    raise credentials_exception

  stmt = select(models.UserModel).where(
      models.UserModel.employee_id == employee_id
  )
  result = await db.execute(stmt)
  user = result.scalars().first()

  if user is None:
    print(f"\n🔥🔥 ПОЛЬЗОВАТЕЛЬ С ID {employee_id} НЕ НАЙДЕН В БД!")
    raise credentials_exception

  return user


async def verify_refresh_token(token: str, db: AsyncSession):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительный или истекший refresh-токен",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        employee_id = payload.get("sub")
        if employee_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(models.UserModel).where(
        models.UserModel.employee_id == int(employee_id)
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user is None or not user.is_active:
        raise credentials_exception
    return user