# Refactoring Demo Project

Учебный проект, демонстрирующий рефакторинг Python-кода: устранение SQL-инъекций, утечек соединений, гонок потоков и небезопасного хранения паролей. Параллельно реализован идентичный сервис на Go.

## Структура проекта

```
.
├── api.py                  # Flask REST API (Python)
├── utils.py                # Утилиты: БД, пароли, активные пользователи
├── requirements.txt        # Python-зависимости
├── openapi.yaml            # Спецификация OpenAPI 3.1
├── Dockerfile.python       # Docker-образ для Flask
├── docker-compose.yml      # Запуск обоих серверов одной командой
├── test_endpoints.py       # Python-скрипт проверки эндпоинтов
├── test_endpoints.sh       # Bash-скрипт (Linux/macOS)
├── test_endpoints.ps1      # PowerShell-скрипт (Windows)
├── go_server/              # Go-реализация того же API
│   ├── main.go
│   ├── Dockerfile
│   ├── go.mod
│   └── internal/
│       ├── db/             # Инициализация SQLite
│       ├── handlers/       # HTTP-хендлеры
│       ├── models/         # Структуры данных
│       └── utils/          # Утилиты (пароли, активные пользователи, JSON)
├── DEPLOY.md               # Гайд: Docker Hub → сервер
├── SERVER_SETUP.md         # Гайд: подключение к серверу и запуск
└── README.md
```

---

## Архитектура

### C4 Level 1 — System Context

```mermaid
C4Context
    title System Context — Refactoring Demo

    Person(user, "Разработчик / Клиент", "Отправляет HTTP-запросы к API")

    System(goApi, "Go API Server", "REST API на Go 1.22\nпорт 8080")
    System(pyApi, "Python Flask API", "REST API на Flask\nпорт 5000")
    SystemDb(sqlite, "SQLite", "Файловая БД users.db\n(отдельная для каждого сервиса)")

    Rel(user, goApi, "HTTP запросы", "JSON / REST")
    Rel(user, pyApi, "HTTP запросы", "JSON / REST")
    Rel(goApi, sqlite, "Читает / Пишет", "CGO · go-sqlite3")
    Rel(pyApi, sqlite, "Читает / Пишет", "sqlite3 (stdlib)")
```

### C4 Level 2 — Container Diagram

```mermaid
C4Container
    title Container Diagram — Refactoring Demo

    Person(client, "Клиент", "curl / тест-скрипт / браузер")

    Container_Boundary(docker, "Docker Compose") {
        Container(goContainer, "go-api", "Go 1.22 · Alpine", "HTTP-сервер\nпорт 8080")
        Container(pyContainer, "python-api", "Python 3.12 · Flask", "HTTP-сервер\nпорт 5000")
        ContainerDb(goDb, "users.db (Go)", "SQLite", "Пользователи Go-сервиса")
        ContainerDb(pyDb, "users.db (Python)", "SQLite", "Пользователи Flask-сервиса")
    }

    Rel(client, goContainer, "REST", "HTTP :8080")
    Rel(client, pyContainer, "REST", "HTTP :5000")
    Rel(goContainer, goDb, "SQL", "go-sqlite3 / CGO")
    Rel(pyContainer, pyDb, "SQL", "sqlite3 stdlib")
```

### C4 Level 3 — Component Diagram (Go Server)

```mermaid
C4Component
    title Component Diagram — Go Server

    Container_Boundary(goServer, "go-api (Go)") {
        Component(router, "ServeMux Router", "net/http", "Маршрутизация запросов\nGo 1.22 pattern routing")
        Component(userH, "User Handler", "handlers/user.go", "POST /adduser\nGET /user/{id}")
        Component(activeH, "Active Handler", "handlers/active.go", "GET|POST /activate/{id}")
        Component(miscH, "Misc Handler", "handlers/misc.go", "GET /\nGET /slow\nGET /wrong")
        Component(dbPkg, "DB Package", "internal/db/db.go", "Открытие пула соединений\nCREATE TABLE IF NOT EXISTS")
        Component(activeUtil, "ActiveUsers Util", "utils/active_users.go", "sync.Mutex\nСписок ≤5 активных ID")
        Component(pwdUtil, "Password Util", "utils/password.go", "SHA-256 + случайная соль")
        Component(respUtil, "Response Util", "utils/response.go", "WriteJSON helper")
        ComponentDb(db, "SQLite DB", "users.db", "Таблица users")
    }

    Rel(router, userH, "вызывает")
    Rel(router, activeH, "вызывает")
    Rel(router, miscH, "вызывает")
    Rel(userH, dbPkg, "использует")
    Rel(activeH, activeUtil, "использует")
    Rel(userH, respUtil, "использует")
    Rel(activeH, respUtil, "использует")
    Rel(miscH, respUtil, "использует")
    Rel(dbPkg, db, "SQL")
```

---

## UML-диаграммы

### Диаграмма классов / структур

```mermaid
classDiagram
    class User {
        +int ID
        +string Name
    }

    class AddUserRequest {
        +string Name
    }

    class AddUserResponse {
        +string Status
        +int ID
        +string Name
    }

    class ActivateResponse {
        +string Status
        +[]int Active
    }

    class ActiveUsers {
        -[]int users
        -sync.Mutex mu
        +Add(uid int)
        +Snapshot() []int
    }

    class DB {
        +Open(path string) *sql.DB
        +AddUser(db, name) (id, error)
        +GetUser(db, uid) (User, error)
    }

    class UserHandler {
        +AddUser(db *sql.DB) HandlerFunc
        +GetUser(db *sql.DB) HandlerFunc
    }

    class ActiveHandler {
        +Activate() HandlerFunc
    }

    class MiscHandler {
        +Index(w, r)
        +Slow(w, r)
        +Wrong(w, r)
    }

    UserHandler --> DB : использует
    UserHandler --> AddUserRequest : парсит
    UserHandler --> AddUserResponse : возвращает
    ActiveHandler --> ActiveUsers : использует
    ActiveHandler --> ActivateResponse : возвращает
    DB --> User : возвращает
```

### Sequence Diagram — POST /adduser

```mermaid
sequenceDiagram
    actor Client
    participant Router as ServeMux
    participant Handler as UserHandler
    participant DB as db.AddUser
    participant SQLite

    Client->>Router: POST /adduser {"name":"Alice"}
    Router->>Handler: вызов AddUser(db)
    Handler->>Handler: json.Decode(body)
    alt name пустое
        Handler-->>Client: 400 {"error":"name is required..."}
    else name валидное
        Handler->>DB: AddUser(db, "Alice")
        DB->>SQLite: INSERT INTO users (name) VALUES (?)
        SQLite-->>DB: lastInsertId = 1
        DB-->>Handler: id=1, err=nil
        Handler-->>Client: 201 {"status":"ok","id":1,"name":"Alice"}
    end
```

### Sequence Diagram — GET /activate/{id}

```mermaid
sequenceDiagram
    actor Client
    participant Router as ServeMux
    participant Handler as ActiveHandler
    participant AU as ActiveUsers (sync.Mutex)

    Client->>Router: GET /activate/42
    Router->>Handler: Activate()
    Handler->>Handler: strconv.Atoi("42")
    alt не число
        Handler-->>Client: 400 {"error":"uid must be an integer"}
    else число
        Handler->>AU: activeMu.Lock()
        AU->>AU: append(42), trim to ≤5
        AU->>Handler: activeMu.Unlock()
        Handler->>AU: Snapshot()
        AU-->>Handler: [38,39,40,41,42]
        Handler-->>Client: 200 {"status":"ok","active":[38,39,40,41,42]}
    end
```

### Sequence Diagram — GET /slow

```mermaid
sequenceDiagram
    actor Client
    participant Handler as MiscHandler
    participant Goroutine as go func()

    Client->>Handler: GET /slow
    Handler->>Goroutine: go func() { sleep 5s }
    Note right of Goroutine: выполняется асинхронно
    Handler-->>Client: 202 {"status":"scheduled"}
    Goroutine->>Goroutine: time.Sleep(5s)
    Goroutine->>Goroutine: log.Println("slow task completed")
```

### State Diagram — жизненный цикл пользователя

```mermaid
stateDiagram-v2
    [*] --> NotExists : начало

    NotExists --> Created : POST /adduser\n(валидное имя)
    NotExists --> Error : POST /adduser\n(пустое имя → 400)

    Created --> Active : GET /activate/{id}
    Active --> Active : GET /activate/{id}\n(обновляет позицию в списке)
    Active --> Evicted : список переполнен\n(>5 активных)
    Evicted --> Active : GET /activate/{id}\n(повторная активация)

    Created --> Retrieved : GET /user/{id} → 200
    Active --> Retrieved : GET /user/{id} → 200
    Evicted --> Retrieved : GET /user/{id} → 200

    NotExists --> NotFound : GET /user/{id} → 404

    Error --> [*]
    NotFound --> [*]
```

### Deployment Diagram

```mermaid
graph TB
    subgraph dev["Локальная машина (Windows)"]
        src["Исходный код\n(go_server/, api.py)"]
        dc["docker-compose.yml"]
    end

    subgraph hub["Docker Hub"]
        img1["matveiv25/refactoring_mv\n:go-server"]
        img2["matveiv25/refactoring_mv\n:python-api"]
    end

    subgraph server["Сервер (Linux VPS)"]
        subgraph compose["docker compose up -d"]
            c1["demo-go-api\n:8080"]
            c2["demo-python-api\n:5000"]
        end
        v1[("go-db volume\nusers.db")]
        v2[("python-db volume\nusers.db")]
    end

    src -->|docker build + push| img1
    src -->|docker build + push| img2
    img1 -->|docker pull| c1
    img2 -->|docker pull| c2
    c1 --- v1
    c2 --- v2
```

---

## Запуск через Docker (рекомендуется)

### Требования

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/) v2+

### Запустить оба сервера

```bash
docker compose up --build
```

- Flask API → `http://localhost:5000`
- Go API → `http://localhost:8080`

### Запустить один сервер

```bash
docker compose up --build go-api      # только Go
docker compose up --build python-api  # только Flask
```

### Остановить

```bash
docker compose down
```

---

## Запуск без Docker

### Python / Flask

```bash
pip install -r requirements.txt
python api.py
# → http://127.0.0.1:5000
```

### Go

```bash
cd go_server
go mod tidy
go run main.go
# → http://localhost:8080
```

---

## Проверка эндпоинтов

```bash
# Go-сервер :8080
python test_endpoints.py

# Flask-сервер :5000
python test_endpoints.py --port 5000

# Оба сервера
python test_endpoints.py --both
```

```powershell
# Windows PowerShell
.\test_endpoints.ps1           # Go :8080
.\test_endpoints.ps1 -Port 5000  # Flask :5000
```

---

## Эндпоинты API

| Метод | URL | Описание | Ответ |
|-------|-----|----------|-------|
| `GET` | `/` | HTML-страница с описанием API | `200` |
| `POST` | `/adduser` | Создать пользователя `{"name":"Alice"}` | `201` / `400` |
| `GET` | `/user/{id}` | Получить пользователя по ID | `200` / `404` |
| `GET\|POST` | `/activate/{id}` | Активировать пользователя | `200` / `400` |
| `GET` | `/slow` | Запустить фоновую задачу (горутина/поток) | `202` |
| `GET` | `/wrong` | Демонстрация обработки ошибок | `500` |

---

## Безопасность

- SQL-запросы параметризованы — SQL-инъекции исключены.
- Пароли хранятся как `pbkdf2_hmac` SHA-256 с солью.
- Соединения с БД управляются через контекстные менеджеры / пул `*sql.DB`.
- Общие структуры данных защищены `threading.Lock` (Python) / `sync.Mutex` (Go).

---

## Docker Hub

Образы опубликованы: [hub.docker.com/r/matveiv25/refactoring_mv](https://hub.docker.com/r/matveiv25/refactoring_mv)

| Тег | Описание |
|-----|----------|
| `go-server` | Go 1.22 + Alpine (~10 МБ) |
| `python-api` | Python 3.12 + Flask |

---

## Документация

| Файл | Содержание |
|------|-----------|
| `openapi.yaml` | OpenAPI 3.1 спецификация всех эндпоинтов |
| `DEPLOY.md` | Полный гайд: Docker Hub → Linux-сервер |
| `SERVER_SETUP.md` | Подключение по SSH и запуск на сервере |
| `go_server/README.md` | Документация Go-сервиса |
| `go_server/GO_GUIDE.md` | Go для Python-разработчика |
