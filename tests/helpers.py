def cookie_payload(
    menu_number: int,
    name: str = "brownie batter",
    price: float = 4.5,
    stock_quantity: int = 50,
    is_available: bool = True,
) -> dict:
    return {
        "name": name,
        "price": price,
        "menu_number": menu_number,
        "is_available": is_available,
        "stock_quantity": stock_quantity,
    }


def login_payload(employee_id: int, pin_code: str) -> dict:
    return {"employee_id": employee_id, "pin_code": pin_code}


def employee_registration_payload(
    employee_id: int,
    name: str,
    pin_code: str,
    role: str,
    is_active: bool = True,
) -> dict:
    return {
        "employee_id": employee_id,
        "name": name,
        "pin_code": pin_code,
        "role": role,
        "is_active": is_active,
    }


def order_payload(box_size: int, cookie_menu_numbers: list[int]) -> dict:
    return {
        "box_size": box_size,
        "cookie_menu_numbers": cookie_menu_numbers,
    }
