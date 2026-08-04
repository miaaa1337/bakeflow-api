from fastapi import FastAPI, HTTPException, Depends, status, Query
from schemas import Cookie, TokenResponse, EmployeeLogin, EmployeeOutput, EmployeeCreate
import schemas
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
import models
from database import engine
from models import UserModel, BOX_PRICES, STANDARD_SINGLE_PRICE, MANAGEMENT_ROLES, BAKE_ALLOWED_ROLES, ALL_ROLES
from collections import Counter
from auth import verify_pin, create_access_token, hash_pin, get_current_user, verify_refresh_token, create_refresh_token
from sqlalchemy import select
from typing import Optional
from sqlalchemy import asc, desc

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

app = FastAPI(title="BakeFlow API")

@app.on_event("startup")
async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

@app.get("/")
async def root():
    return {"status": "working", "project": "BakeFlow"}

@app.post("/cookies/", status_code=status.HTTP_201_CREATED)
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


@app.post("/cookies/{menu_number}/bake", status_code=status.HTTP_201_CREATED)
async def baked_cookie(menu_number: int, amount: int, db: AsyncSession = Depends(get_db), current_user: models.UserModel = Depends(get_current_user)):
    if current_user.role not in BAKE_ALLOWED_ROLES:
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


@app.post("/cookies/{menu_number}/buy", status_code=status.HTTP_200_OK)
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

@app.post("/orders/", status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: schemas.OrderCreate, db: AsyncSession = Depends(get_db)):
  # 1. Проверяем размер коробки
  if order_data.box_size not in BOX_PRICES:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Неверный размер коробки. Доступны варианты только на 1, 3 или 6"
        " шт.",
    )
  # 2. Проверяем соответствие количества выбранных печений
  if len(order_data.cookie_menu_numbers) != order_data.box_size:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            f"Количество печений ({len(order_data.cookie_menu_numbers)}) не"
            f" соответствует размеру коробки ({order_data.box_size})."
        ),
    )

  # Считаем сколько штук каждого печенья запрашивают (например, {1: 1, 2: 1, 3: 1})
  requested_counts = Counter(order_data.cookie_menu_numbers)

  total_extra = 0.0

  # 3. Валидация наличия и расчет наценок
  for menu_num, qty in requested_counts.items():
    stmt = select(models.CookieModel).where(models.CookieModel.menu_number == menu_num)
    result = await db.execute(stmt)
    db_cookie = result.scalars().first()

    if not db_cookie:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Печенье №{menu_num} не найдено.",
      )

    if db_cookie.stock_quantity < qty:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=(
              f"Недостаточно печенья №{menu_num} на складе! Запрошено: {qty},"
              f" осталось: {db_cookie.stock_quantity}."
          ),
      )

    # Наценка за спешл-печенье умножается на qty этого конкретного печенья!
    extra_charge = max(0.0, db_cookie.price - STANDARD_SINGLE_PRICE)
    total_extra += extra_charge * qty

  # 4. Списание со склада
  for menu_num, qty in requested_counts.items():
    stmt = select(models.CookieModel).where(models.CookieModel.menu_number == menu_num)
    result = await db.execute(stmt)
    db_cookie = result.scalars().first()

    # Списываем ровно столько штук этого вида, сколько заказали!
    db_cookie.stock_quantity -= qty
    if db_cookie.stock_quantity == 0:
      db_cookie.is_available = False

  # 5. Итоговый расчет и сохранение заказа
  base_box_price = BOX_PRICES[order_data.box_size]
  total = round(base_box_price + total_extra, 2)

  new_order = models.OrderModel(
      box_size=order_data.box_size, total_price=total
  )

  db.add(new_order)
  await db.flush()
  for menu_num, qty in requested_counts.items():
      stmt = select(models.CookieModel).where(models.CookieModel.menu_number == menu_num)
      result = await db.execute(stmt)
      db_cookie = result.scalars().first()

      order_item = models.OrderItemModel(
          order_id=new_order.id, cookie_id=db_cookie.id, quantity=qty
      )
      db.add(order_item)


  await db.commit()
  await db.refresh(new_order)

  return {
        "message": (
            f"Заказ оформлен! Коробка на {order_data.box_size} шт. Сумма:"
            f" ${total}"
        ),
        "order": new_order,
    }


@app.get("/orders/", response_model=list[schemas.OrderResponse],
    status_code=status.HTTP_200_OK,)
async def get_all_orders(db: AsyncSession = Depends(get_db)):
   orders = await db.execute(select(models.OrderModel))
   return orders.scalars().all()

@app.get("/orders/{order_id}",
    response_model=schemas.OrderResponse,
    status_code=status.HTTP_200_OK,
)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
  stmt = select(models.OrderModel).where(models.OrderModel.id == order_id)
  result = await db.execute(stmt)
  db_order = result.scalars().first()
  if not db_order:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Заказ №{order_id} не найден.",
    )
  return db_order

@app.get("/cookies/", status_code=status.HTTP_200_OK)
async def get_all_cookies(
   limit: int = Query(10, ge=1, le=100, description="Количество записей на страницу"),
   offset: int = Query(0, ge=0, description="Смещение" ),
   search: Optional[str] = Query(None, description="Поиск по названию"),
   sort_by: str = Query("id", regex="^(id|name|price)$", description="Поле для сортировки"),
   order: str = Query("asc", regex="^(asc|desc)$", description="Порядок: asc или desc"),
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


@app.get("/cookies/{menu_number}", status_code=status.HTTP_200_OK)
async def get_cookie(menu_number: int, db: AsyncSession = Depends(get_db)):
    stmt = select(models.CookieModel).where(models.CookieModel.menu_number == menu_number)
    result = await db.execute(stmt)
    db_cookie = result.scalars().first()
    if db_cookie:
        return {"data": db_cookie}
    else:
        raise HTTPException(status_code=404, detail=f"Печенье №{menu_number} не найдено.")

@app.delete("/cookies/{menu_number}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cookie(menu_number: int, db: AsyncSession = Depends(get_db)):
    stmt = select(models.CookieModel).where(models.CookieModel.menu_number == menu_number)
    result = await db.execute(stmt)
    db_cookie = result.scalars().first()
    if db_cookie:
        await db.delete(db_cookie)
        await db.commit()
        return 
    else:
     raise HTTPException(status_code=404, detail=f"Печенье №{menu_number} не найдено.")

@app.put("/cookies/{menu_number}", status_code=status.HTTP_200_OK)
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


@app.post("/login", response_model=TokenResponse)
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

@app.post("/register", response_model=EmployeeOutput)
async def register_new_employee(data: EmployeeCreate, db: AsyncSession = Depends(get_db), current_user: models.UserModel = Depends(get_current_user)):
   if current_user.role != models.ROLE_MANAGER:
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
      pin_code_hash= hashed_pin
   )
   db.add(new_employee)
   await db.commit()
   await db.refresh(new_employee)
   return new_employee

@app.get("/me")
async def get_me(current_user: models.UserModel = Depends(get_current_user)):
   return current_user

@app.post("/refresh")
async def refresh_token(data: schemas.RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
   user = await verify_refresh_token(data.refresh_token, db)
   new_access = create_access_token(data={"sub": str(user.employee_id), "role": user.role})
   new_refresh = create_refresh_token(data={"sub": str(user.employee_id)})
   return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }

