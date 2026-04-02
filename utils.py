import sqlite3
import threading
import time
import json
import hashlib
import os
from contextlib import contextmanager
from typing import Optional

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

DB_PATH = "users.db"


@contextmanager
def db_connection(path: str = DB_PATH):
    """Контекстный менеджер: гарантирует закрытие соединения."""
    conn = sqlite3.connect(path)
    try:
        yield conn
    finally:
        conn.close()


def init_db(path: str = DB_PATH) -> None:
    """Создаёт таблицу users, если она ещё не существует."""
    with db_connection(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT    NOT NULL,
                tags TEXT    NOT NULL DEFAULT '[]'
            )
            """
        )
        conn.commit()


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

def add_user(name: str, tags: Optional[list] = None) -> int:
    """
    Добавляет пользователя в базу.

    Args:
        name: имя пользователя.
        tags: список тегов (не изменяется у вызывающего кода).

    Returns:
        int — id созданной записи.
    """
    # Работаем с копией, чтобы не мутировать аргумент вызывающего кода
    user_tags = list(tags) if tags is not None else []
    user_tags.append("new")

    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, tags) VALUES (?, ?)",
            (name, json.dumps(user_tags)),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_user_by_name(name: str) -> Optional[dict]:
    """
    Ищет пользователя по имени.

    Returns:
        dict с ключами id, name, tags (list[str]) или None, если не найден.
    """
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, tags FROM users WHERE name = ?",
            (name,),
        )
        row = cur.fetchone()

    if not row:
        return None

    uid, uname, tags_json = row
    try:
        tags = json.loads(tags_json)
        if not isinstance(tags, list):
            tags = []
    except (json.JSONDecodeError, TypeError):
        tags = []

    # Гарантируем список строк
    tags = [str(t) for t in tags]
    return {"id": uid, "name": uname, "tags": tags}


# ---------------------------------------------------------------------------
# Password storage
# ---------------------------------------------------------------------------

def _hash_password(password: str) -> str:
    """
    Хеширует пароль через pbkdf2_hmac (SHA-256, 260 000 итераций).

    Returns:
        Строка вида «hex_salt$hex_hash».
    """
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
    return f"{salt.hex()}${dk.hex()}"


def store_password(user_id: int, password: str) -> None:
    """Сохраняет хеш пароля в файл. Формат строки: user_id:salt$hash."""
    hashed = _hash_password(password)
    with open("passwords.txt", "a") as f:
        f.write(f"{user_id}:{hashed}\n")


# ---------------------------------------------------------------------------
# Active users (потокобезопасно)
# ---------------------------------------------------------------------------

_active_users: list = []
_active_users_lock = threading.Lock()


def set_active(user_id: int, max_active: int = 5) -> None:
    """
    Добавляет user_id в список активных пользователей.
    Хранит не более max_active последних ID. Потокобезопасен.
    """
    with _active_users_lock:
        _active_users.append(user_id)
        # Удаляем лишние записи с начала списка
        excess = len(_active_users) - max_active
        if excess > 0:
            del _active_users[:excess]


def get_active_users_snapshot() -> list:
    """Возвращает копию списка активных пользователей (потокобезопасно)."""
    with _active_users_lock:
        return list(_active_users)


# ---------------------------------------------------------------------------
# Admin check
# ---------------------------------------------------------------------------

def is_admin(user: object) -> bool:
    """
    Возвращает True только если user — dict с ключом 'role' == 'admin'.
    Любые другие значения (None, строка, int и т.п.) → False.
    При ошибках никогда не возвращает True.
    """
    if not isinstance(user, dict):
        return False
    return user.get("role") == "admin"


# ---------------------------------------------------------------------------
# Long-running task
# ---------------------------------------------------------------------------

def long_running_task(n: int) -> int:
    """Вычисляет сумму квадратов от 1 до n включительно."""
    return n * (n + 1) * (2 * n + 1) // 6


def run_long_running_task_in_thread(n: int, callback=None) -> threading.Thread:
    """
    Запускает long_running_task в отдельном потоке.

    Args:
        n:        аргумент для long_running_task.
        callback: необязательная функция(result), вызываемая по завершении.

    Returns:
        Запущенный поток (daemon=True).
    """
    def _worker():
        result = long_running_task(n)
        if callback is not None:
            callback(result)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test() -> None:
    """Базовые проверки корректности модуля."""
    import tempfile, os

    # Используем временную БД, чтобы не засорять рабочую
    tmp_db = tempfile.mktemp(suffix=".db")
    original_db = globals().get("DB_PATH", "users.db")

    # Патчим DB_PATH на время теста
    import utils as _self
    _self.DB_PATH = tmp_db
    init_db(tmp_db)

    try:
        # 1. add_user возвращает int
        original_tags = ["vip"]
        uid = add_user("Alice", original_tags)
        assert isinstance(uid, int), f"add_user должен вернуть int, получили {type(uid)}"

        # 2. Вызывающий список не изменился
        assert original_tags == ["vip"], "add_user не должен мутировать переданный список тегов"

        # 3. Пользователь реально создан и имеет тег "new"
        user = get_user_by_name("Alice")
        assert user is not None, "Пользователь Alice должен существовать"
        assert "new" in user["tags"], f"Тег 'new' должен присутствовать, tags={user['tags']}"

        # 4. Несуществующий пользователь → None
        assert get_user_by_name("Ghost") is None, "Несуществующий пользователь должен вернуть None"

        # 5. is_admin
        assert is_admin({"role": "admin"}) is True
        assert is_admin({"role": "user"}) is False
        assert is_admin(None) is False
        assert is_admin("admin") is False
        assert is_admin(42) is False

        # 6. Активные пользователи
        for i in range(7):
            set_active(i, max_active=5)
        snapshot = get_active_users_snapshot()
        assert len(snapshot) <= 5, f"Снапшот должен содержать ≤5 элементов, получили {len(snapshot)}"
        assert snapshot == list(range(2, 7)), f"Ожидали [2,3,4,5,6], получили {snapshot}"

        # 7. store_password пишет файл
        pw_file = tmp_db + "_passwords.txt"
        import builtins
        _orig_open = builtins.open

        written_lines = []

        def _mock_open(file, mode="r", **kwargs):
            if file == "passwords.txt" and "a" in mode:
                import io
                buf = io.StringIO()
                class _W:
                    def write(self, s): written_lines.append(s)
                    def __enter__(self): return self
                    def __exit__(self, *a): pass
                return _W()
            return _orig_open(file, mode, **kwargs)

        builtins.open = _mock_open
        try:
            store_password(uid, "s3cr3t")
        finally:
            builtins.open = _orig_open

        assert len(written_lines) == 1, "store_password должна записать одну строку"
        assert written_lines[0].startswith(f"{uid}:"), "Строка должна начинаться с user_id"
        assert "$" in written_lines[0], "Строка должна содержать разделитель salt$hash"

        print("self_test: все проверки пройдены успешно.")

    finally:
        _self.DB_PATH = original_db
        if os.path.exists(tmp_db):
            os.remove(tmp_db)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()

    # Запускаем self_test
    self_test()

    # Демонстрация потокобезопасного добавления активных пользователей
    threads = [
        threading.Thread(target=set_active, args=(uid,), daemon=True)
        for uid in range(10)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("Снапшот активных пользователей:", get_active_users_snapshot())
