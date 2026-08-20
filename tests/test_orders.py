import pytest
from tests.helpers import login_payload, order_payload, cookie_payload

@pytest.mark.asyncio
async def test_create_order_success(authenticated_ac, ac):
    test_cookie_1 = cookie_payload(95)
    await authenticated_ac.post("/cookies/", json=test_cookie_1)
    test_cookie_2 = cookie_payload(94)
    await authenticated_ac.post("/cookies/", json=test_cookie_2)
    test_cookie_3 = cookie_payload(93)
    await authenticated_ac.post("/cookies/", json=test_cookie_3)
    baked_cookies = [95, 94, 93]
    order_data = order_payload(3, baked_cookies)
    response = await ac.post("/orders/", json= order_data)
    assert response.status_code == 201
    stock_1 = await ac.get("/cookies/95")
    assert stock_1.status_code == 200
    cookie_95_data = stock_1.json()["data"]
    assert cookie_95_data["stock_quantity"] == 49

@pytest.mark.asyncio
async def test_create_order_not_founded(authenticated_ac, ac):
    test_cookie_1 = cookie_payload(95)
    await authenticated_ac.post("/cookies/", json=test_cookie_1)
    test_cookie_2 = cookie_payload(94)
    await authenticated_ac.post("/cookies/", json=test_cookie_2)
    baked_cookies = [95, 94, 93]
    order_data = order_payload(3, baked_cookies)
    response = await ac.post("/orders/", json= order_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Печенье №93 не найдено."

@pytest.mark.asyncio
async def test_create_order_invalid_box_size(authenticated_ac, ac):
    test_cookie_1 = cookie_payload(95)
    await authenticated_ac.post("/cookies/", json=test_cookie_1)
    test_cookie_2 = cookie_payload(94)
    await authenticated_ac.post("/cookies/", json=test_cookie_2)
    test_cookie_3 = cookie_payload(93)
    await authenticated_ac.post("/cookies/", json=test_cookie_3)
    baked_cookies = [95, 94, 93]
    order_data = order_payload(4, baked_cookies)
    response = await ac.post("/orders/", json= order_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Неверный размер коробки. Доступны варианты только на 1, 3 или 6 шт."

@pytest.mark.asyncio
async def test_create_order_not_enough(authenticated_ac, ac):
    test_cookie_1 = cookie_payload(95, "brownie batter", 4.5, 1, True)
    await authenticated_ac.post("/cookies/", json=test_cookie_1)
    test_cookie_2 = cookie_payload(94)
    await authenticated_ac.post("/cookies/", json=test_cookie_2)
    baked_cookies = [95, 95, 94]
    order_data = order_payload(3, baked_cookies)
    response = await ac.post("/orders/", json= order_data)
    assert response.status_code == 400
    assert response.json()["detail"] == f"Недостаточно печенья №95 на складе! Запрошено: 2, осталось: 1."

@pytest.mark.asyncio
async def test_create_order_invalid_size(authenticated_ac, ac):
    test_cookie_1 = cookie_payload(95)
    await authenticated_ac.post("/cookies/", json=test_cookie_1)
    test_cookie_2 = cookie_payload(94)
    await authenticated_ac.post("/cookies/", json=test_cookie_2)
    test_cookie_3 = cookie_payload(93)
    await authenticated_ac.post("/cookies/", json=test_cookie_3)
    baked_cookies = [95, 94, 93, 94]
    order_data = order_payload(3, baked_cookies)
    response = await ac.post("/orders/", json= order_data)
    assert response.status_code == 400
    assert response.json()["detail"] == f"Количество печений (4) не соответствует размеру коробки (3)."

@pytest.mark.asyncio
async def test_create_order_not_available(authenticated_ac, ac):
    test_cookie_1 = cookie_payload(95, "brownie batter", 4.5, 10, False)
    await authenticated_ac.post("/cookies/", json=test_cookie_1)
    test_cookie_2 = cookie_payload(94)
    await authenticated_ac.post("/cookies/", json=test_cookie_2)
    baked_cookies = [95, 95, 94]
    order_data = order_payload(3, baked_cookies)
    response = await ac.post("/orders/", json= order_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "печенья нет в наличии"


@pytest.mark.asyncio
async def test_buy_cookie_success(authenticated_ac, ac):
    test_cookie_1 = cookie_payload(95)
    await authenticated_ac.post("/cookies/", json=test_cookie_1)
    response = await ac.post("/cookies/95/buy", params={"amount": 30})
    assert response.status_code == 200
    stock = await ac.get("/cookies/95")
    assert stock.status_code == 200
    cookie_95_data = stock.json()["data"]
    assert cookie_95_data["stock_quantity"] == 20

@pytest.mark.asyncio
async def test_buy_cookie_not_found(ac):
    response = await ac.post("/cookies/95/buy", params={"amount": 30})
    assert response.status_code == 404
    assert response.json()["detail"] == "Печенье №95 не найдено."

@pytest.mark.asyncio
async def test_buy_cookie_insufficient_stock(authenticated_ac, ac):
    test_cookie_1 = cookie_payload(95)
    await authenticated_ac.post("/cookies/", json=test_cookie_1)
    response = await ac.post("/cookies/95/buy", params={"amount": 55})
    assert response.status_code == 400
    assert response.json()["detail"] == "Недостаточно печений на складе! Доступно: 50, вы запросили: 55."

@pytest.mark.asyncio
async def test_buy_cookie_invalid_amount(authenticated_ac, ac):
    test_cookie_1 = cookie_payload(95)
    await authenticated_ac.post("/cookies/", json=test_cookie_1)
    response = await ac.post("/cookies/95/buy", params={"amount": -5})
    assert response.status_code == 400
    assert response.json()["detail"] == "Кол-во печенья для покупки не может быть меньше или равно 0."

@pytest.mark.asyncio
async def test_get_all_orders(authenticated_ac, ac):
    test_cookie_1 = cookie_payload(95)
    await authenticated_ac.post("/cookies/", json=test_cookie_1)
    test_cookie_2 = cookie_payload(94)
    await authenticated_ac.post("/cookies/", json=test_cookie_2)
    test_cookie_3 = cookie_payload(93)
    await authenticated_ac.post("/cookies/", json=test_cookie_3)
    baked_cookies = [95, 94, 93]
    order_data = order_payload(3, baked_cookies)
    response = await ac.post("/orders/", json= order_data)
    assert response.status_code == 201
    order_1 = await ac.get("/orders/")
    assert order_1.status_code == 200
    orders = order_1.json()
    assert isinstance(orders, list)
    assert len(orders) == 1
    assert orders[0]["box_size"] == 3

@pytest.mark.asyncio
async def test_get_no_orders(ac):
    response = await ac.get("/orders/")
    assert response.status_code == 404
    assert response.json()["detail"] == "нет существующих заказов"

@pytest.mark.asyncio
async def test_get_order_by_id(authenticated_ac, ac):
    test_cookie_1 = cookie_payload(95)
    await authenticated_ac.post("/cookies/", json=test_cookie_1)
    test_cookie_2 = cookie_payload(94)
    await authenticated_ac.post("/cookies/", json=test_cookie_2)
    test_cookie_3 = cookie_payload(93)
    await authenticated_ac.post("/cookies/", json=test_cookie_3)
    baked_cookies = [95, 94, 93]
    order_data = order_payload(3, baked_cookies)
    create_response = await ac.post("/orders/", json= order_data)
    assert create_response.status_code == 201
    order_id = create_response.json()["order"]["id"]
    response = await ac.get(f"/orders/{order_id}")
    assert response.status_code == 200
    order = response.json()
    assert order["id"] == order_id
    assert order["box_size"] == 3

@pytest.mark.asyncio
async def test_get_order_not_found(ac):
    response = await ac.get("/orders/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Заказ №999 не найден."
    
