from collections import Counter
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
import models
import schemas
from models import UserModel, BOX_PRICES, STANDARD_SINGLE_PRICE, MANAGEMENT_ROLES, BAKE_ALLOWED_ROLES, ALL_ROLES, ROLE_MANAGER
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: schemas.OrderCreate, db: AsyncSession = Depends(get_db)):
  # 1. Проверяем размер коробки
  if order_data.box_size not in BOX_PRICES:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Неверный размер коробки. Доступны варианты только на 1, 3 или 6 шт.",
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

    # Проверяем доступность ДО списания
    if not db_cookie.is_available:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="печенья нет в наличии"
      )

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

@router.get("/", response_model=list[schemas.OrderResponse],
    status_code=status.HTTP_200_OK,)
async def get_all_orders(db: AsyncSession = Depends(get_db)):
   stmt = select(models.OrderModel).options(selectinload(models.OrderModel.items))
   result = await db.execute(stmt)
   orders = result.scalars().all()
   if not orders:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                detail="нет существующих заказов")
   return orders


@router.get("/{order_id}",
    response_model=schemas.OrderResponse,
    status_code=status.HTTP_200_OK,
)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
  stmt = select(models.OrderModel).where(models.OrderModel.id == order_id).options(selectinload(models.OrderModel.items))
  result = await db.execute(stmt)
  db_order = result.scalars().first()
  if not db_order:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Заказ №{order_id} не найден.",
    )
  return db_order