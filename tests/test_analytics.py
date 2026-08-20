import pytest


@pytest.mark.asyncio
async def test_get_summary(authenticated_ac):
    """Тест получения общей бизнес-статистики"""
    response = await authenticated_ac.get("/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_orders" in data
    assert "total_revenue" in data

@pytest.mark.asyncio
async def test_get_summary_bad_request(ac):
    response = await ac.get("/analytics/summary")
    assert response.status_code == 401
    assert response.json()["detail"] == "Авторизация не выполнена"

@pytest.mark.asyncio
async def test_get_popular_cookies(authenticated_ac):
    """Тест получения рейтинга популярных печенек"""
    response = await authenticated_ac.get("/analytics/popular?limit_val=3")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_popular_cookies_failed(ac):
    response = await ac.get("/analytics/popular?limit_val=3")
    assert response.status_code == 401
    assert response.json()["detail"] == "Авторизация не выполнена"


@pytest.mark.asyncio
async def test_get_low_stock(authenticated_ac):
    """Тест получения списка печенек с низким остатком"""
    response = await authenticated_ac.get("/analytics/low-stock?threshold=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_low_stock_failed(ac):
    response = await ac.get("/analytics/low-stock?threshold=10")
    assert response.status_code == 401
    assert response.json()["detail"] == "Авторизация не выполнена"
