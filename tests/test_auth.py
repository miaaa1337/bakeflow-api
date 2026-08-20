import pytest

from tests.helpers import login_payload, employee_registration_payload


@pytest.mark.asyncio
async def test_login_success(authenticated_ac):
    login_data = login_payload(54, "1337")
    response = await authenticated_ac.post("/login", json=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(ac):
    login_data = login_payload(111, "1338")
    response = await ac.post("/login", json=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный ID или PIN"

@pytest.mark.asyncio
async def test_login_deactivated(emp_inv_ac):
    login_data = login_payload(57, "3434")
    response = await emp_inv_ac.post("/login", json=login_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Сотрудник деактивирован"


@pytest.mark.asyncio
async def test_get_me(authenticated_ac):
    response = await authenticated_ac.get("/me")
    assert response.status_code == 200
    data = response.json()
    assert data["employee_id"] == 54
    assert data["role"] == "manager"

@pytest.mark.asyncio
async def test_get_me_invalid(ac):
    login_data = login_payload(55, "1338")
    log_res = await ac.post("/login", json=login_data)
    response = await ac.get("/me")
    assert response.status_code == 401
    


@pytest.mark.asyncio
async def test_refresh_token_success(ac):
    login_data = login_payload(54, "1337")
    log_res = await ac.post("/login", json=login_data)
    refresh_token = log_res.json()["refresh_token"]
    refresh_payload = {"refresh_token": refresh_token}
    response = await ac.post("/refresh", json=refresh_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_refresh_rejects_malformed_token(ac):
    login = login_payload(54, "1337")
    log_res = await ac.post("/login", json=login)
    refresh_token = log_res.json()["refresh_token"]
    invalid_refresh_token = refresh_token + "1"
    refresh_payload = {"refresh_token": invalid_refresh_token}
    response = await ac.post("/refresh", json=refresh_payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Недействительный или истекший refresh-токен"

@pytest.mark.asyncio
async def test_refresh_rejects_access_token(ac):
    login = login_payload(54, "1337")
    log_res = await ac.post("/login", json=login)
    token = log_res.json()["access_token"]
    refresh_payload = {"refresh_token": token}
    response = await ac.post("/refresh", json=refresh_payload)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_employee_registration_success(authenticated_ac):
    registration = employee_registration_payload(22, "New Emp", "4443", "shift_lead", True)
    response = await authenticated_ac.post("/register", json= registration)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_employee_registration_failed(employee_ac):
    registration = employee_registration_payload(22, "New Emp", "4443", "shift_lead", True)
    response = await employee_ac.post("/register", json= registration)
    assert response.status_code == 403
    assert response.json()["detail"] == "Только менеджер может регистрировать новых сотрудников!"

@pytest.mark.asyncio
async def test_employee_registration_already_exists(authenticated_ac):
    registration = employee_registration_payload(22, "New Emp", "4443", "shift_lead", True)
    await authenticated_ac.post("/register", json= registration)
    repeat_reg = employee_registration_payload(22, "New Emp", "4443", "shift_lead", True)
    response = await authenticated_ac.post("/register", json= repeat_reg)
    assert response.status_code == 400
    assert response.json()["detail"] == "Сотрудник с таким ID уже существует"
