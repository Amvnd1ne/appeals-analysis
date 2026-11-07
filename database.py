"""
Модуль для работы с базой данных SQLite.
Содержит функции инициализации БД и получения соединения.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "support.db"


def get_connection():
    """Возвращает соединение с БД с доступом к колонкам по имени."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создаёт таблицы, если их ещё нет."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS appeals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            text TEXT NOT NULL,
            category TEXT,
            user_name TEXT,
            status TEXT DEFAULT 'new'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            keywords TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS appeal_tags (
            appeal_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (appeal_id, tag_id),
            FOREIGN KEY (appeal_id) REFERENCES appeals(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    """)

    default_categories = [
        ("Оплата", "оплата,платеж,оплатить,деньги,списание,возврат,карта"),
        ("Доставка", "доставка,курьер,посылка,отправление,срок,заказ,трек"),
        ("Техническая проблема", "ошибка,баг,не работает,сломалось,глючит,вылетает,зависает"),
        ("Личный кабинет", "вход,логин,пароль,аккаунт,регистрация,профиль,авторизация"),
        ("Качество товара", "брак,качество,дефект,поврежден,не соответствует,сломан"),
        ("Консультация", "вопрос,как,подскажите,консультация,информация,уточнить"),
    ]
    for name, keywords in default_categories:
        cur.execute(
            "INSERT OR IGNORE INTO categories (name, keywords) VALUES (?, ?)",
            (name, keywords),
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"База данных инициализирована {DB_PATH}")