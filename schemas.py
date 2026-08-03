from pydantic import BaseModel, Field 
from datetime import datetime

class Cookie(BaseModel):
    menu_number: int = Field(gt=0, description="Номер печенья в меню должен быть больше 0")
    name: str = Field(min_length=2, max_length=100)
    price: float = Field(gt=0, description="Цена должна быть больше 0")
    is_available: bool = True
    stock_quantity: int = Field(default=0, ge=0, description="Количество на складе")

class OrderCreate(BaseModel):
    box_size: int = Field(..., description="Размер коробки: 1, 3 или 6 штук")
    cookie_menu_numbers: list[int] = Field(..., description="Номер печенья в меню")

class OrderItemResponse(BaseModel):
    cookie_id: int
    quantity: int

    class Config:
      from_attributes = True

class OrderResponse(BaseModel):
    id: int
    box_size: int
    total_price: float
    created_at: datetime
    items: list[OrderItemResponse]

    class Config:
      from_attributes = True 

class EmployeeLogin(BaseModel): 
   employee_id: int
   pin_code: str

class TokenResponse(BaseModel):
   access_token: str
   refresh_token: str
   token_type: str = "bearer"

class EmployeeOutput(BaseModel):
   id: int
   employee_id: int
   name: str
   role: str
   is_active: bool

   class Config:
         from_attributes = True

class EmployeeCreate(BaseModel):
    employee_id: int
    name: str
    pin_code: str
    role: str

class RefreshTokenRequest(BaseModel):
    resresh_token: str