#!/usr/bin/env bash
# Проверка всех эндпоинтов API.
# Использование:
#   ./test_endpoints.sh          # Go-сервер на :8080 (по умолчанию)
#   ./test_endpoints.sh 5000     # Python/Flask-сервер на :5000

PORT=${1:-8080}
BASE="http://localhost:$PORT"
PASS=0
FAIL=0

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

check() {
  local label="$1"
  local expected_status="$2"
  local actual_status="$3"
  local body="$4"

  if [ "$actual_status" -eq "$expected_status" ]; then
    echo -e "${GREEN}[PASS]${NC} $label → HTTP $actual_status"
    PASS=$((PASS + 1))
  else
    echo -e "${RED}[FAIL]${NC} $label → expected HTTP $expected_status, got HTTP $actual_status"
    FAIL=$((FAIL + 1))
  fi
  echo "       $body"
  echo
}

echo -e "${CYAN}=== Testing API on $BASE ===${NC}"
echo

# ---------------------------------------------------------------------------
# POST /adduser — успешное создание
# ---------------------------------------------------------------------------
resp=$(curl -s -w "\n%{http_code}" -X POST "$BASE/adduser" \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice"}')
body=$(echo "$resp" | head -n1)
status=$(echo "$resp" | tail -n1)
check "POST /adduser (valid name)" 201 "$status" "$body"

# Сохраняем ID для следующих тестов
USER_ID=$(echo "$body" | grep -o '"id":[0-9]*' | grep -o '[0-9]*')

# ---------------------------------------------------------------------------
# POST /adduser — пустое имя → 400
# ---------------------------------------------------------------------------
resp=$(curl -s -w "\n%{http_code}" -X POST "$BASE/adduser" \
  -H "Content-Type: application/json" \
  -d '{"name":""}')
body=$(echo "$resp" | head -n1)
status=$(echo "$resp" | tail -n1)
check "POST /adduser (empty name → 400)" 400 "$status" "$body"

# ---------------------------------------------------------------------------
# POST /adduser — нет поля name → 400
# ---------------------------------------------------------------------------
resp=$(curl -s -w "\n%{http_code}" -X POST "$BASE/adduser" \
  -H "Content-Type: application/json" \
  -d '{}')
body=$(echo "$resp" | head -n1)
status=$(echo "$resp" | tail -n1)
check "POST /adduser (missing name → 400)" 400 "$status" "$body"

# ---------------------------------------------------------------------------
# GET /user/{id} — пользователь найден
# ---------------------------------------------------------------------------
resp=$(curl -s -w "\n%{http_code}" "$BASE/user/${USER_ID:-1}")
body=$(echo "$resp" | head -n1)
status=$(echo "$resp" | tail -n1)
check "GET /user/$USER_ID (found → 200)" 200 "$status" "$body"

# ---------------------------------------------------------------------------
# GET /user/{id} — не найден → 404
# ---------------------------------------------------------------------------
resp=$(curl -s -w "\n%{http_code}" "$BASE/user/99999")
body=$(echo "$resp" | head -n1)
status=$(echo "$resp" | tail -n1)
check "GET /user/99999 (not found → 404)" 404 "$status" "$body"

# ---------------------------------------------------------------------------
# GET /activate/{id}
# ---------------------------------------------------------------------------
resp=$(curl -s -w "\n%{http_code}" "$BASE/activate/${USER_ID:-1}")
body=$(echo "$resp" | head -n1)
status=$(echo "$resp" | tail -n1)
check "GET /activate/$USER_ID (→ 200)" 200 "$status" "$body"

# ---------------------------------------------------------------------------
# POST /activate/{id}
# ---------------------------------------------------------------------------
resp=$(curl -s -w "\n%{http_code}" -X POST "$BASE/activate/${USER_ID:-1}")
body=$(echo "$resp" | head -n1)
status=$(echo "$resp" | tail -n1)
check "POST /activate/$USER_ID (→ 200)" 200 "$status" "$body"

# ---------------------------------------------------------------------------
# GET /slow
# ---------------------------------------------------------------------------
resp=$(curl -s -w "\n%{http_code}" "$BASE/slow")
body=$(echo "$resp" | head -n1)
status=$(echo "$resp" | tail -n1)
check "GET /slow (→ 202)" 202 "$status" "$body"

# ---------------------------------------------------------------------------
# GET /wrong
# ---------------------------------------------------------------------------
resp=$(curl -s -w "\n%{http_code}" "$BASE/wrong")
body=$(echo "$resp" | head -n1)
status=$(echo "$resp" | tail -n1)
check "GET /wrong (→ 500)" 500 "$status" "$body"

# ---------------------------------------------------------------------------
# Итог
# ---------------------------------------------------------------------------
echo -e "${CYAN}=== Results ===${NC}"
echo -e "${GREEN}PASS: $PASS${NC}  ${RED}FAIL: $FAIL${NC}"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
