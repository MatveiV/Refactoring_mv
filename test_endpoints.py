"""
Проверка всех эндпоинтов API.

Использование:
    python test_endpoints.py              # Go-сервер на :8080 (по умолчанию)
    python test_endpoints.py --port 5000  # Python/Flask-сервер на :5000
    python test_endpoints.py --both       # Проверить оба сервера последовательно
"""

import argparse
import sys
import urllib.request
import urllib.error
import json as _json


# ---------------------------------------------------------------------------
# HTTP helper (без внешних зависимостей)
# ---------------------------------------------------------------------------

def request(method: str, url: str, body: dict | None = None) -> tuple[int, dict]:
    data = _json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, _json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, _json.loads(e.read())
        except Exception:
            return e.code, {}


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
HEAD = "\033[96m"
RST  = "\033[0m"


def check(label: str, expected: int, actual: int, body: dict) -> bool:
    ok = actual == expected
    tag = PASS if ok else FAIL
    print(f"{tag} {label}")
    print(f"       HTTP {actual}  {_json.dumps(body, ensure_ascii=False)}")
    print()
    return ok


def run_suite(base: str) -> int:
    """Запускает все тесты против base URL. Возвращает количество провалов."""
    passed = failed = 0

    print(f"{HEAD}=== Testing API on {base} ==={RST}\n")

    # ------------------------------------------------------------------
    # POST /adduser — успешное создание
    # ------------------------------------------------------------------
    status, body = request("POST", f"{base}/adduser", {"name": "Alice"})
    ok = check("POST /adduser  (valid name → 201)", 201, status, body)
    passed, failed = (passed + ok, failed + (not ok))
    user_id = body.get("id", 1)

    # ------------------------------------------------------------------
    # POST /adduser — пустое имя → 400
    # ------------------------------------------------------------------
    status, body = request("POST", f"{base}/adduser", {"name": ""})
    ok = check("POST /adduser  (empty name → 400)", 400, status, body)
    passed, failed = (passed + ok, failed + (not ok))

    # ------------------------------------------------------------------
    # POST /adduser — отсутствует поле name → 400
    # ------------------------------------------------------------------
    status, body = request("POST", f"{base}/adduser", {})
    ok = check("POST /adduser  (missing name → 400)", 400, status, body)
    passed, failed = (passed + ok, failed + (not ok))

    # ------------------------------------------------------------------
    # GET /user/{id} — пользователь найден → 200
    # ------------------------------------------------------------------
    status, body = request("GET", f"{base}/user/{user_id}")
    ok = check(f"GET  /user/{user_id}  (found → 200)", 200, status, body)
    passed, failed = (passed + ok, failed + (not ok))

    # ------------------------------------------------------------------
    # GET /user/{id} — не найден → 404
    # ------------------------------------------------------------------
    status, body = request("GET", f"{base}/user/99999")
    ok = check("GET  /user/99999  (not found → 404)", 404, status, body)
    passed, failed = (passed + ok, failed + (not ok))

    # ------------------------------------------------------------------
    # GET /activate/{id} → 200
    # ------------------------------------------------------------------
    status, body = request("GET", f"{base}/activate/{user_id}")
    ok = check(f"GET  /activate/{user_id}  (→ 200)", 200, status, body)
    passed, failed = (passed + ok, failed + (not ok))

    # ------------------------------------------------------------------
    # POST /activate/{id} → 200
    # ------------------------------------------------------------------
    status, body = request("POST", f"{base}/activate/{user_id}")
    ok = check(f"POST /activate/{user_id}  (→ 200)", 200, status, body)
    passed, failed = (passed + ok, failed + (not ok))

    # ------------------------------------------------------------------
    # GET /slow → 202
    # ------------------------------------------------------------------
    status, body = request("GET", f"{base}/slow")
    ok = check("GET  /slow  (→ 202)", 202, status, body)
    passed, failed = (passed + ok, failed + (not ok))

    # ------------------------------------------------------------------
    # GET /wrong → 500
    # ------------------------------------------------------------------
    status, body = request("GET", f"{base}/wrong")
    ok = check("GET  /wrong  (→ 500)", 500, status, body)
    passed, failed = (passed + ok, failed + (not ok))

    # ------------------------------------------------------------------
    # Итог
    # ------------------------------------------------------------------
    color = "\033[92m" if failed == 0 else "\033[91m"
    print(f"{color}Results: {passed} passed, {failed} failed{RST}\n")
    return failed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="API endpoint tester")
    parser.add_argument("--port", type=int, default=8080,
                        help="Port to test (default: 8080)")
    parser.add_argument("--both", action="store_true",
                        help="Test both servers: Go :8080 and Flask :5000")
    args = parser.parse_args()

    total_failures = 0

    if args.both:
        total_failures += run_suite("http://localhost:8080")
        total_failures += run_suite("http://localhost:5000")
    else:
        total_failures += run_suite(f"http://localhost:{args.port}")

    sys.exit(1 if total_failures > 0 else 0)


if __name__ == "__main__":
    main()
