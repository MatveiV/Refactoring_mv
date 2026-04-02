import sqlite3
import threading
import time
from flask import Flask, request, jsonify, g

app = Flask(__name__)

DB_PATH = "test.db"

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Возвращает соединение с БД, привязанное к текущему контексту запроса."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception: BaseException | None = None) -> None:
    """Закрывает соединение с БД по завершении контекста запроса."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.before_first_request
def init_db() -> None:
    """Создаёт таблицу users при первом запросе, если она ещё не существует."""
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
        """
    )
    db.commit()


# ---------------------------------------------------------------------------
# /adduser  — создание пользователя
# ---------------------------------------------------------------------------

@app.route("/adduser", methods=["POST"])
def add_user():
    data = request.get_json(silent=True) or {}
    name = data.get("name")

    if not name or not isinstance(name, str) or not name.strip():
        return jsonify({"error": "name is required and must be a non-empty string"}), 400

    name = name.strip()
    db = get_db()
    cursor = db.execute("INSERT INTO users (name) VALUES (?)", (name,))
    db.commit()
    user_id = cursor.lastrowid

    return jsonify({"status": "ok", "id": user_id, "name": name}), 201


# ---------------------------------------------------------------------------
# /user/<uid>  — получение пользователя по ID
# ---------------------------------------------------------------------------

@app.route("/user/<int:uid>", methods=["GET"])
def get_user(uid: int):
    db = get_db()
    row = db.execute(
        "SELECT id, name FROM users WHERE id = ?", (uid,)
    ).fetchone()

    if row is None:
        return jsonify({"error": "not_found"}), 404

    return jsonify({"id": row["id"], "name": row["name"]}), 200


# ---------------------------------------------------------------------------
# Active users (потокобезопасно)
# ---------------------------------------------------------------------------

_active_users: list[int] = []
_active_lock = threading.Lock()


def add_active_user(user_id: int, max_active: int = 5) -> None:
    """Добавляет user_id в список активных (не более max_active последних)."""
    with _active_lock:
        _active_users.append(user_id)
        excess = len(_active_users) - max_active
        if excess > 0:
            del _active_users[:excess]


def get_active_users() -> list[int]:
    """Возвращает потокобезопасную копию списка активных пользователей."""
    with _active_lock:
        return list(_active_users)


@app.route("/activate/<int:uid>", methods=["GET", "POST"])
def activate(uid: int):
    add_active_user(uid)
    return jsonify({"status": "ok", "active": get_active_users()}), 200


# ---------------------------------------------------------------------------
# /slow  — тяжёлая задача в отдельном потоке
# ---------------------------------------------------------------------------

def _slow_task(n: int) -> None:
    """Имитирует долгую работу (запускается в фоновом потоке)."""
    time.sleep(n)


@app.route("/slow", methods=["GET"])
def slow():
    delay = 5
    thread = threading.Thread(target=_slow_task, args=(delay,), daemon=True)
    thread.start()
    return jsonify({"status": "scheduled"}), 202


# ---------------------------------------------------------------------------
# /wrong  — демонстрация обработки ошибок
# ---------------------------------------------------------------------------

@app.route("/wrong", methods=["GET"])
def wrong():
    try:
        result = 1 / 0
    except ZeroDivisionError:
        return jsonify({"msg": "error", "detail": "division by zero"}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
