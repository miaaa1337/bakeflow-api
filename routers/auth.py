from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_pin,
    verify_pin,
    verify_refresh_token,
)
from database import get_db
import models
import schemas
from schemas import TokenResponse, EmployeeLogin, EmployeeOutput, EmployeeCreate
from models import ALL_ROLES


router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def employee_login(data: EmployeeLogin, db: AsyncSession = Depends(get_db)):
   stmt = select(models.UserModel).where(models.UserModel.employee_id == data.employee_id)
   result = await db.execute(stmt)
   db_employee = result.scalars().first()
   if not db_employee:
      raise HTTPException(status_code=401, detail="Неверный ID или PIN")
   if not verify_pin(data.pin_code, db_employee.pin_code_hash):
      raise HTTPException(status_code=401, detail="Неверный ID или PIN")
   if not db_employee.is_active:
      raise HTTPException(status_code=403, detail="Сотрудник деактивирован")
   access_token = create_access_token(data={"sub": str(db_employee.employee_id), "role": db_employee.role})
   ref_token = create_refresh_token(data={"sub": str(db_employee.employee_id), "role": db_employee.role})
   return {
        "access_token": access_token,
        "refresh_token": ref_token,
        "token_type": "bearer"
   }


@router.post("/register", response_model=EmployeeOutput)
async def register_new_employee(data: EmployeeCreate, db: AsyncSession = Depends(get_db), current_user: models.UserModel = Depends(get_current_user)):
   if current_user.role not in models.MANAGEMENT_ROLES:
       raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN, 
           detail="Только менеджер может регистрировать новых сотрудников!"
       )
   result = await db.execute(select(models.UserModel).where(models.UserModel.employee_id == data.employee_id))
   existing_emp = result.scalars().first()
   if existing_emp:
      raise HTTPException(status_code=400, detail="Сотрудник с таким ID уже существует")
   if data.role not in ALL_ROLES:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail=f"Недопустимая роль. Выберите из: {', '.join(ALL_ROLES)}"
    )
   hashed_pin = hash_pin(data.pin_code)
   new_employee = models.UserModel( 
      employee_id= data.employee_id, 
      name= data.name,
      role= data.role,
      pin_code_hash= hashed_pin,
      is_active = data.is_active,
   )
   db.add(new_employee)
   await db.commit()
   await db.refresh(new_employee)
   return new_employee


@router.get("/me")
async def get_me(current_user: models.UserModel = Depends(get_current_user)):
  return current_user


@router.post("/refresh")
async def refresh_token(data: schemas.RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
   user = await verify_refresh_token(data.refresh_token, db)
   new_access = create_access_token(data={"sub": str(user.employee_id), "role": user.role})
   new_refresh = create_refresh_token(data={"sub": str(user.employee_id)})
   return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }