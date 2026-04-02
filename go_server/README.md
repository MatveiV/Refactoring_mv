# Go User Service

Полный порт Python/Flask-сервиса на Go. Сохраняет все эндпоинты оригинала,
обеспечивает безопасную работу с SQLite, потокобезопасный доступ к общим
структурам данных и корректную обработку ошибок.

## Что внутри

| Файл | Описание |
|------|----------|
| `main.go` | Всё приложение: роутер, хендлеры, работа с БД, утилиты |
| `go.mod` | Зависимости модуля |
| `users.db` | SQLite-база (создаётся автоматически при первом запуске) |

---

## Требования

- Go 1.22+ — https://go.dev/dl/
- GCC (нужен для компиляции `go-sqlite3` через CGO)
  - Windows: [TDM-GCC](https://jmeubank.github.io/tdm-gcc/) или MinGW-w64
  - macOS: `xcode-select --install`
  - Linux: `sudo apt install gcc` / `sudo dnf install gcc`

---

## Запуск через Docker (рекомендуется)

Не требует установки Go или GCC — всё собирается внутри контейнера.

```bash
# из корня проекта
cd go_server

# собрать образ
docker build -t go-server .

# запустить контейнер
docker run --rm -p 8080:8080 go-server
```

Сервер будет доступен на `http://localhost:8080`.

Остановить контейнер: `Ctrl+C` (флаг `--rm` удалит его автоматически).

---

## Установка зависимостей

```bash
go mod tidy
```

Команда скачает `github.com/mattn/go-sqlite3` и обновит `go.sum`.

---

## Запуск без Docker

```bash
go run main.go
```

Сервер поднимется на `http://localhost:8080`.

---

## Сборка бинарного файла

```bash
go build -o server main.go
```

После сборки запускать так:

```bash
# Linux / macOS
./server

# Windows
server.exe
```

Бинарник можно скопировать на любую машину с той же ОС и архитектурой —
Go компилирует в самодостаточный исполняемый файл.

Кросс-компиляция (например, Linux-бинарник на Windows):

```bash
GOOS=linux GOARCH=amd64 go build -o server_linux main.go
```

---

## Эндпоинты

### `POST /adduser` — создать пользователя

Тело запроса (JSON):

```json
{ "name": "Alice" }
```

Параметры тела:

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `name` | string | да | Непустое имя пользователя |

Ответы:

| Статус | Тело |
|--------|------|
| `201 Created` | `{"status":"ok","id":1,"name":"Alice"}` |
| `400 Bad Request` | `{"error":"name is required and must be a non-empty string"}` |
| `500 Internal Server Error` | `{"error":"db error"}` |

Пример:

```bash
curl -X POST http://localhost:8080/adduser \
     -H "Content-Type: application/json" \
     -d '{"name":"Alice"}'
```

---

### `GET /user/{uid}` — получить пользователя по ID

Параметры пути:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `uid` | integer | Числовой ID пользователя |

Ответы:

| Статус | Тело |
|--------|------|
| `200 OK` | `{"id":1,"name":"Alice"}` |
| `404 Not Found` | `{"error":"not_found"}` |
| `400 Bad Request` | `{"error":"uid must be an integer"}` |

Пример:

```bash
curl http://localhost:8080/user/1
```

---

### `GET /activate/{uid}` — активировать пользователя

Добавляет пользователя в in-memory список активных (хранится не более 5 последних).
Операция потокобезопасна через `sync.Mutex`.

Параметры пути:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `uid` | integer | ID пользователя для активации |

Ответ `200 OK`:

```json
{ "status": "ok", "active": [3, 4, 5, 6, 7] }
```

Пример:

```bash
curl http://localhost:8080/activate/42
```

---

### `GET /slow` — запуск тяжёлой задачи в фоне

Запускает горутину с `time.Sleep(5s)` и сразу возвращает ответ, не блокируя сервер.

Ответ `202 Accepted`:

```json
{ "status": "scheduled" }
```

Пример:

```bash
curl http://localhost:8080/slow
```

---

### `GET /wrong` — демонстрация обработки ошибок

Возвращает корректный JSON-ответ вместо паники или пустого тела.

Ответ `500 Internal Server Error`:

```json
{ "msg": "error", "detail": "division by zero" }
```

Пример:

```bash
curl http://localhost:8080/wrong
```

---

## Утилиты (внутренние функции)

| Функция | Описание |
|---------|----------|
| `initDB()` | Открывает `users.db` и создаёт таблицу `users` через `CREATE TABLE IF NOT EXISTS` |
| `addActiveUser(uid)` | Потокобезопасно добавляет ID в список; удаляет лишние с начала при превышении лимита |
| `getActiveUsersSnapshot()` | Возвращает копию списка активных пользователей под мьютексом |
| `hashPassword(password)` | Генерирует случайную соль (16 байт), хеширует SHA-256; формат: `hex_salt$hex_hash` |
| `writeJSON(w, status, payload)` | Устанавливает `Content-Type: application/json`, статус и сериализует тело |

---

## Отличия от Python/Flask версии

| Аспект | Python/Flask | Go |
|--------|--------------|----|
| Соединение с БД | `flask.g` + `@teardown_appcontext` | Один `*sql.DB` на всё приложение (пул соединений встроен) |
| Потокобезопасность | `threading.Lock` | `sync.Mutex` |
| Фоновые задачи | `threading.Thread` | горутина (`go func()`) |
| Роутинг | Flask декораторы | `http.NewServeMux` (Go 1.22 pattern routing) |
| Порт | 5000 | 8080 |
