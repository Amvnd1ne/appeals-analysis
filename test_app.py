"""
Тесты для веб-приложения «Анализ обращений».
Запуск: pytest test_app.py -v
"""
import pytest

from app import app
from database import get_connection, init_db


@pytest.fixture
def client():
    """Тестовый клиент Flask."""
    init_db()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_index_returns_200(client):
    """Главная страница открывается."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Обращения пользователей".encode("utf-8") in resp.data


def test_stats_page_returns_200(client):
    """Страница статистики открывается."""
    resp = client.get("/stats")
    assert resp.status_code == 200
    assert "Статистика обращений".encode("utf-8") in resp.data


def test_api_stats_returns_json(client):
    """REST API /api/stats отдаёт корректный JSON."""
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total" in data
    assert "by_category" in data
    assert "by_status" in data
    assert isinstance(data["total"], int)


def test_api_appeals_with_filter(client):
    """REST API /api/appeals фильтрует по категории."""
    resp = client.get("/api/appeals?category=Оплата&limit=3")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "count" in data
    assert "appeals" in data
    for a in data["appeals"]:
        assert a["category"] == "Оплата"


def test_export_csv_returns_file(client):
    """Экспорт CSV отдаёт файл с правильным заголовком."""
    resp = client.get("/export/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["Content-Type"]
    assert "attachment" in resp.headers["Content-Disposition"]


def test_search_filters_results(client):
    """Поиск по слову «доставка» фильтрует обращения."""
    resp = client.get("/?q=доставка")
    assert resp.status_code == 200
    assert "Найдено обращений".encode("utf-8") in resp.data


def test_appeal_detail_404_for_unknown(client):
    """Несуществующее обращение — 404."""
    resp = client.get("/appeal/999999")
    assert resp.status_code == 404


def test_database_has_categories():
    """В БД есть стартовые категории."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM categories")
    cnt = cur.fetchone()["cnt"]
    conn.close()
    assert cnt >= 6