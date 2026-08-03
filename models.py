from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

ROLE_BAKER = "baker"
ROLE_LEAD_BAKER = "lead_baker"
ROLE_SHIFT_LEAD = "shift_lead"
ROLE_MANAGER = "manager"

ALL_ROLES = [ROLE_BAKER, ROLE_LEAD_BAKER, ROLE_SHIFT_LEAD, ROLE_MANAGER]

BAKE_ALLOWED_ROLES = [ROLE_LEAD_BAKER, ROLE_SHIFT_LEAD, ROLE_MANAGER]
MANAGEMENT_ROLES = [ROLE_SHIFT_LEAD, ROLE_MANAGER]



STANDARD_SINGLE_PRICE = 4.99
BOX_PRICES = {
    1: 4.99,   # Коробка на 1 шт
    3: 13.99,  # Коробка на 3 шт (выгоднее!)
    6: 23.99   # Коробка на 6 шт (самый большой дисконт!)
}
class CookieModel(Base):
    __tablename__ = "cookies"

    id = Column(Integer, primary_key=True, index=True) # Уникальный ID каждой записи
    menu_number = Column(Integer, unique=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    is_available = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    items = relationship("OrderItemModel", back_populates="order")
    box_size = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)  
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 

class OrderItemModel(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    cookie_id = Column(Integer, ForeignKey("cookies.id"), nullable=False)
    quantity = Column(Integer)
    order = relationship("OrderModel", back_populates="items")
    cookie = relationship("CookieModel")

class UserModel(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index= True)
    employee_id = Column(Integer, unique=True, index=True, nullable=False)
    pin_code_hash = Column(String, nullable=False)
    role = Column(String, default="baker")
    is_active = Column(Boolean, default=True)
