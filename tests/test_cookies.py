import pytest
from tests.helpers import cookie_payload


@pytest.mark.asyncio
async def test_create_cookie(authenticated_ac):
    new_cookie = cookie_payload(99)
    response = await authenticated_ac.post("/cookies/", json=new_cookie)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_duplicate_menu_number(authenticated_ac):
    cookie_data = cookie_payload(55)
    await authenticated_ac.post("/cookies/", json=cookie_data)
    response = await authenticated_ac.post("/cookies/", json=cookie_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Печенье с номером 55 уже существует."

@pytest.mark.asyncio
async def test_create_cookie_unauthorized(ac):
    new_cookie = cookie_payload(100, name="secret cookie", price=5.0, stock_quantity=10)
    response = await ac.post("/cookies/", json=new_cookie)
    assert response.status_code in (401, 403, 400)


@pytest.mark.asyncio
async def test_create_cookie_forbidden_role(employee_ac):
    # employee_ac это baker - не может создавать печенья
    new_cookie = cookie_payload(100)
    response = await employee_ac.post("/cookies/", json=new_cookie)
    assert response.status_code == 400
    assert "Недостаточно прав" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_all_cookies(ac):
    response = await ac.get("/cookies/")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_special_cookie(authenticated_ac):
    test_cookie = cookie_payload(98, name="brownie batter")
    await authenticated_ac.post("/cookies/", json=test_cookie)
    response = await authenticated_ac.get("/cookies/98")
    assert response.status_code == 200
    res_json = response.json()
    assert "data" in res_json
    assert res_json["data"]["name"] == "brownie batter"
    assert res_json["data"]["menu_number"] == 98


@pytest.mark.asyncio
async def test_not_founded_cookie(ac):
    response = await ac.get("/cookies/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Печенье №9999 не найдено."


@pytest.mark.asyncio
async def test_delete_cookie(authenticated_ac):
    test_cookie = cookie_payload(97)
    await authenticated_ac.post("/cookies/", json=test_cookie)
    response = await authenticated_ac.delete("/cookies/97")
    assert response.status_code == 204

    get_res = await authenticated_ac.get("/cookies/97")
    assert get_res.status_code == 404
    assert get_res.json()["detail"] == "Печенье №97 не найдено."


@pytest.mark.asyncio
async def test_update_cookie_success(authenticated_ac):
    test_cookie = cookie_payload(96)
    await authenticated_ac.post("/cookies/", json=test_cookie)
    updated_test_cookie = cookie_payload(96, name="brownie cheesecake", stock_quantity=75)
    response = await authenticated_ac.put("/cookies/96", json=updated_test_cookie)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "brownie cheesecake"


@pytest.mark.asyncio
async def test_update_cookie_not_found(authenticated_ac):
    updated_test_cookie = cookie_payload(996, name="brownie cheesecake", stock_quantity=75)
    response = await authenticated_ac.put("/cookies/996", json=updated_test_cookie)
    assert response.status_code == 404
    assert response.json()["detail"] == "Печенье №996 не найдено."


@pytest.mark.asyncio
async def test_bake_cookies(authenticated_ac):
    test_cookie = cookie_payload(95)
    await authenticated_ac.post("/cookies/", json=test_cookie)
    baked = {"amount": 100}
    response = await authenticated_ac.post("/cookies/95/bake", params=baked)
    data = response.json()
    assert response.status_code == 201
    assert "Выпечено 100 печений №95. Текущее количество на складе: 150" in data["message"]


@pytest.mark.asyncio
async def test_bake_cookie_not_found(authenticated_ac):
    baked = {"amount": 100}
    response = await authenticated_ac.post("/cookies/23/bake", params=baked)
    assert response.status_code == 404
    assert response.json()["detail"] == "Печенье №23 не найдено."


@pytest.mark.asyncio
async def test_bake_cookie_invalid_amount(authenticated_ac):
    test_cookie = cookie_payload(94)
    await authenticated_ac.post("/cookies/", json=test_cookie)
    baked = {"amount": -5}
    response = await authenticated_ac.post("/cookies/94/bake", params=baked)
    assert response.status_code == 400
    assert response.json()["detail"] == "Количество печенья для выпечки должно быть больше 0."


@pytest.mark.asyncio
async def test_bake_cookie_forbidden(authenticated_ac, employee_ac):
    test_cookie = cookie_payload(94)
    await authenticated_ac.post("/cookies/", json=test_cookie)

    response = await employee_ac.post("/cookies/94/bake", params={"amount": 100})

    assert response.status_code == 403
    assert response.json()["detail"] == "Недостаточно прав для добавления выпечки!"