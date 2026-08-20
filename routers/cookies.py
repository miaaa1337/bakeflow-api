from typing import Optional
from auth import get_current_user
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
import models
import schemas
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from models import UserModel, BOX_PRICES, STANDARD_SINGLE_PRICE, MANAGEMENT_ROLES, BAKE_ALLOWED_ROLES, ALL_ROLES, ROLE_MANAGER
from schemas import Cookie

router = APIRouter(prefix="/cookies", tags=["Cookies"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_cookie(cookie: Cookie, db: AsyncSession= Depends(get_db), current_user: models.UserModel = Depends(get_current_user)):
   if current_user.role not in MANAGEMENT_ROLES:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Недостаточно прав для создания нового печенья")
   stmt = select(models.CookieModel).where(models.CookieModel.menu_number == cookie.menu_number)
   result = await db.execute(stmt)
   exisiting_cookie = result.scalars().first()
   if exisiting_cookie:
        raise HTTPException(status_code=400, detail=f"Печенье с номером {cookie.menu_number} уже существует.")
   else:
        new_cookie = models.CookieModel(
        menu_number=cookie.menu_number,
        name=cookie.name,
        price=cookie.price,
        is_available=cookie.is_available,
        stock_quantity=cookie.stock_quantity
    )
        db.add(new_cookie)
        await db.commit()
        await db.refresh(new_cookie)
        return {"message": "Печенье успешно добавлено!", "data": cookie}


@router.post("/{menu_number}/bake", status_code=status.HTTP_201_CREATED)
async def baked_cookie(menu_number: int, amount: int, db: AsyncSession = Depends(get_db), current_user: models.UserModel = Depends(get_current_user)):
    if current_user.role not in models.MANAGEMENT_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,  detail="Недостаточно прав для добавления выпечки!")
    stmt = select(models.CookieModel).where(models.CookieModel.menu_number == menu_number)
    result = await db.execute(stmt)
    db_cookie = result.scalars().first()
    if not db_cookie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Печенье №{menu_number} не найдено.")
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Количество печенья для выпечки должно быть больше 0.")
    db_cookie.stock_quantity += amount
    if db_cookie.stock_quantity > 0 and not db_cookie.is_available:
        db_cookie.is_available = True
    await db.commit()
    return {"message": f"Выпечено {amount} печений №{menu_number}. Текущее количество на складе: {db_cookie.stock_quantity}, добавлено в базу данных сотрудником {current_user.name}."}



@router.post("/{menu_number}/buy", status_code=status.HTTP_200_OK)
async def sold_cookie(menu_number: int,amount: int, db: AsyncSession = Depends(get_db)):
    stmt = select(models.CookieModel).where(models.CookieModel.menu_number == menu_number)
    result = await db.execute(stmt)
    db_cookie = result.scalars().first()
    if not db_cookie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Печенье №{menu_number} не найдено.")
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Кол-во печенья для покупки не может быть меньше или равно 0.")
    if db_cookie.stock_quantity < amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Недостаточно печений на складе! Доступно: {db_cookie.stock_quantity}, вы запросили: {amount}.")
    db_cookie.stock_quantity -= amount
    if db_cookie.stock_quantity == 0:
        db_cookie.is_available = False
    await db.commit()
    await db.refresh(db_cookie)
    return{ "message": f"Продано {amount} печенек. Текущее количество на складе: {db_cookie.stock_quantity}.",
        "data": db_cookie}

@router.get("/", status_code=status.HTTP_200_OK)
async def get_all_cookies(
   limit: int = Query(10, ge=1, le=100, description="Количество записей на страницу"),
   offset: int = Query(0, ge=0, description="Смещение" ),
   search: Optional[str] = Query(None, description="Поиск по названию"),
   sort_by: str = Query("id", pattern="^(id|name|price)$", description="Поле для сортировки"),
   order: str = Query("asc", pattern="^(asc|desc)$", description="Порядок: asc или desc"),
   db: AsyncSession = Depends(get_db)
   ):
    query = select(models.CookieModel)
    if search:
       query = query.where(models.CookieModel.name.ilike(f"%{search}%"))
    if sort_by:
       sort_column = getattr(models.CookieModel, sort_by)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))  
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    cookies =  result.scalars().all()
    return {"data": cookies}


@router.get("/{menu_number}", status_code=status.HTTP_200_OK)
async def get_cookie(menu_number: int, db: AsyncSession = Depends(get_db)):
    stmt = select(models.CookieModel).where(models.CookieModel.menu_number == menu_number)
    result = await db.execute(stmt)
    db_cookie = result.scalars().first()
    if db_cookie:
        return {"data": db_cookie}
    else:
        raise HTTPException(status_code=404, detail=f"Печенье №{menu_number} не найдено.")


@router.delete("/{menu_number}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cookie(menu_number: int, db: AsyncSession = Depends(get_db),current_user: models.UserModel = Depends(get_current_user)):
    if current_user.role not in MANAGEMENT_ROLES:
              raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Недостаточно прав для внедрения изменений")   
    stmt = select(models.CookieModel).where(models.CookieModel.menu_number == menu_number)
    result = await db.execute(stmt)
    db_cookie = result.scalars().first()
    if db_cookie:
        await db.delete(db_cookie)
        await db.commit()
        return 
    else:
     raise HTTPException(status_code=404, detail=f"Печенье №{menu_number} не найдено.")


@router.put("/{menu_number}", status_code=status.HTTP_200_OK)
async def update_cookie(cookie: Cookie, menu_number: int, db: AsyncSession = Depends(get_db), current_user: models.UserModel = Depends(get_current_user)):
    if current_user.role not in MANAGEMENT_ROLES:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Недостаточно прав для внедрения изменений")
    stmt = select(models.CookieModel).where(models.CookieModel.menu_number == menu_number)
    result = await db.execute(stmt)
    db_cookie = result.scalars().first()
    if db_cookie:
        db_cookie.name = cookie.name
        db_cookie.price = cookie.price
        db_cookie.is_available = cookie.is_available
        await db.commit()
        return {"message": f"Печенье №{menu_number} успешно обновлено!", "data": cookie}
    else:
        raise HTTPException(status_code=404, detail=f"Печенье №{menu_number} не найдено.")
