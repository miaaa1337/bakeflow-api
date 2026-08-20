from fastapi import APIRouter, Depends
from sqlalchemy import func, select, literal
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import models
from models import OrderModel, CookieModel, OrderItemModel
from auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from models import UserModel,  MANAGEMENT_ROLES, BAKE_ALLOWED_ROLES, ALL_ROLES, ROLE_MANAGER

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db) , current_user: models.UserModel = Depends(get_current_user)):
    # Пример подсчёта общей выручки и количества заказов
    if current_user.role not in MANAGEMENT_ROLES:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail=f"Авторизация не выполнена")
    result = await db.execute(
        select(
            func.count(OrderModel.id).label("total_orders"),
            func.coalesce(func.sum(OrderModel.total_price), 0).label("total_revenue")
        )
    )
    stats = result.mappings().one()
    return stats

@router.get("/popular")
async def most_popular_cookies(limit_val: int = 5, db: AsyncSession = Depends(get_db), current_user: models.UserModel = Depends(get_current_user)):
    """Топ самых продаваемых печенек"""
    if current_user.role not in MANAGEMENT_ROLES:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail=f"Авторизация не выполнена")
    stmt = (
        select(
            CookieModel.id,
            CookieModel.name,
            func.sum(OrderItemModel.quantity).label("total_sold")
        )
        .join(OrderItemModel, CookieModel.id == OrderItemModel.cookie_id)
        .group_by(CookieModel.id, CookieModel.name)
        .order_by(func.sum(OrderItemModel.quantity).desc())
        .limit(literal(limit_val))
    )
    result = await db.execute(stmt)
    # mappings().all() превращает результат в удобный список словарей
    return result.mappings().all()

@router.get("/low-stock")
async def get_low_stock(threshold: int = 10, db: AsyncSession = Depends(get_db), current_user: models.UserModel = Depends(get_current_user)):
    """Печенья, которые заканчиваются на складе (меньше threshold)"""
    if current_user.role not in MANAGEMENT_ROLES:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail=f"Авторизация не выполнена")
    stmt = select(CookieModel).where(CookieModel.stock_quantity < threshold)
    result = await db.execute(stmt)
    return result.scalars().all()


