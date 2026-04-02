# Go для Python-разработчика: разбор на примере этого проекта

---

## Почему Go, а не Python?

Честный ответ: Go не «лучше» Python в абсолютном смысле. Это разные инструменты.
Но у Go есть конкретные преимущества, которые важны для серверного кода.

| Критерий | Python | Go |
|----------|--------|----|
| Скорость выполнения | Медленный (интерпретатор) | В 10–50 раз быстрее (компилируется в машинный код) |
| Потребление памяти | Высокое | Низкое |
| Параллелизм | GIL мешает настоящей многопоточности | Горутины — миллионы лёгких потоков |
| Типизация | Динамическая (ошибки в рантайме) | Статическая (ошибки на этапе компиляции) |
| Деплой | Нужен интерпретатор + зависимости | Один бинарный файл, без зависимостей |
| Старт сервера | Секунды | Миллисекунды |
| Читаемость | Очень высокая | Высокая, но строже |

### Где Go выигрывает у Python

- Высоконагруженные API (тысячи запросов в секунду)
- Микросервисы и контейнеры (маленький бинарник = маленький Docker-образ)
- Системные утилиты и CLI-инструменты
- Всё, где важна предсказуемая латентность
- Многопоточная обработка данных

### Где Python остаётся лучшим выбором

- Data Science, ML, AI (numpy, pandas, torch — экосистема несравнима)
- Быстрые прототипы и скрипты
- Автоматизация и DevOps-скрипты
- Проекты, где скорость разработки важнее скорости выполнения

---

## Основы Go на примере этого проекта

Разберём `main.go` по частям — от простого к сложному.

---

### 1. Пакеты и импорты

```go
package main

import (
    "database/sql"
    "encoding/json"
    "net/http"
    "sync"

    _ "github.com/mattn/go-sqlite3"
)
```

В Python ты пишешь `import flask`. В Go то же самое, но строже:

- `package main` — каждый файл принадлежит пакету. `main` — точка входа программы.
- Импорты в круглых скобках — просто стиль Go для группировки.
- `_ "github.com/mattn/go-sqlite3"` — импорт ради побочного эффекта (регистрация драйвера SQLite). Аналог `import sqlite3` в Python, но Go требует явно указать, что имя не используется.
- Неиспользуемый импорт — **ошибка компиляции**. Go не позволяет мусорить в коде.

---

### 2. Переменные и типы

Python:
```python
active_users = []
max_active = 5
name = "Alice"
```

Go:
```go
var activeUsers []int      // явное объявление с типом
const maxActiveUsers = 5   // константа
name := "Alice"            // короткое объявление, тип выводится автоматически
```

Ключевые отличия:
- Типы **обязательны** (или выводятся компилятором — это называется type inference).
- `:=` — объявить и присвоить одновременно (только внутри функций).
- `var` — объявление на уровне пакета или когда нужен явный тип.
- `const` — неизменяемое значение, вычисляется на этапе компиляции.

В нашем проекте:
```go
// main.go
const maxActiveUsers = 5

var (
    activeUsers []int    // срез (аналог list в Python)
    activeMu    sync.Mutex
)
```

---

### 3. Функции

Python:
```python
def add_user(name: str, tags: list = None) -> int:
    ...
```

Go:
```go
func addActiveUser(uid int) {
    // нет возвращаемого значения — аналог None
}

func getActiveUsersSnapshot() []int {
    // возвращает срез int
}
```

Особенности:
- Тип параметра пишется **после** имени: `uid int`, а не `int uid`.
- Возвращаемый тип — после скобок.
- Go поддерживает **несколько возвращаемых значений** — это идиома для обработки ошибок:

```go
res, err := db.Exec("INSERT INTO users (name) VALUES (?)", body.Name)
if err != nil {
    // обработка ошибки
}
```

В Python ты бы написал `try/except`. В Go ошибка — это просто второе возвращаемое значение.
Это заставляет явно обрабатывать каждую ошибку — никаких скрытых исключений.

---

### 4. Структуры вместо классов

В Go нет классов. Вместо них — структуры (`struct`).

Python:
```python
class User:
    def __init__(self, name: str):
        self.name = name
```

Go:
```go
type User struct {
    ID   int    `json:"id"`
    Name string `json:"name"`
}
```

В нашем проекте структуры используются для парсинга JSON-тела запроса:

```go
// main.go — handleAddUser
var body struct {
    Name string `json:"name"`
}
json.NewDecoder(r.Body).Decode(&body)
```

`json:"name"` — это **тег структуры**. Он говорит JSON-декодеру: поле `Name` в Go
соответствует ключу `"name"` в JSON. Аналог `pydantic` в Python, но встроен в язык.

---

### 5. Горутины — параллелизм без боли

Python страдает от GIL (Global Interpreter Lock) — настоящей многопоточности нет.
Для параллелизма нужны `asyncio`, `multiprocessing` или внешние библиотеки.

В Go параллелизм встроен в язык через **горутины**:

```go
// main.go — handleSlow
go func() {
    time.Sleep(5 * time.Second)
    log.Println("slow task completed")
}()
```

`go` перед вызовом функции — запустить её в горутине. Всё. Одно слово.

Горутина — это не поток ОС. Go управляет тысячами горутин на нескольких потоках ОС.
Стоимость одной горутины — ~2 КБ памяти против ~1 МБ для потока ОС.

Сравни с Python-версией:
```python
# api.py
thread = threading.Thread(target=_slow_task, args=(delay,), daemon=True)
thread.start()
```

В Go это просто `go _slowTask(delay)`.

---

### 6. Мьютексы — потокобезопасность

Когда несколько горутин читают/пишут одни данные, нужна синхронизация.

Python:
```python
_active_lock = threading.Lock()
with _active_lock:
    _active_users.append(user_id)
```

Go:
```go
// main.go
var activeMu sync.Mutex

func addActiveUser(uid int) {
    activeMu.Lock()
    defer activeMu.Unlock()   // выполнится при выходе из функции
    activeUsers = append(activeUsers, uid)
}
```

`defer` — ключевое слово Go. Откладывает выполнение до конца функции.
Это гарантирует, что мьютекс всегда разблокируется, даже если функция завершится с ошибкой.
Аналог `finally` в Python, но элегантнее.

---

### 7. Работа с базой данных

Python (наш utils.py):
```python
with db_connection() as conn:
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, tags) VALUES (?, ?)", (name, tags))
    conn.commit()
    return int(cur.lastrowid)
```

Go:
```go
// main.go — handleAddUser
res, err := db.Exec("INSERT INTO users (name) VALUES (?)", body.Name)
if err != nil {
    writeJSON(w, http.StatusInternalServerError, ...)
    return
}
id, _ := res.LastInsertId()
```

В Go `*sql.DB` — это **пул соединений**, а не одно соединение. Он сам управляет
открытием/закрытием соединений. Не нужен контекстный менеджер — пул делает это автоматически.

Параметризованные запросы (`?`) работают так же, как в Python — защита от SQL-инъекций.

---

### 8. HTTP-сервер без фреймворка

Python требует Flask или FastAPI для удобного роутинга.
Go 1.22 добавил pattern routing прямо в стандартную библиотеку:

```go
// main.go
mux := http.NewServeMux()
mux.HandleFunc("POST /adduser", handleAddUser)
mux.HandleFunc("GET /user/{uid}", handleGetUser)
mux.HandleFunc("GET /activate/{uid}", handleActivate)

http.ListenAndServe(":8080", mux)
```

`{uid}` — именованный параметр пути. Получить его:
```go
uidStr := r.PathValue("uid")
```

Никаких внешних зависимостей. Flask в Python — это отдельный пакет.
В Go HTTP-сервер — часть стандартной библиотеки.

---

### 9. Обработка ошибок

Python использует исключения:
```python
try:
    result = 1 / 0
except ZeroDivisionError:
    return jsonify({"error": "division by zero"}), 500
```

Go не имеет исключений. Ошибка — это значение:
```go
value, err := someFunction()
if err != nil {
    // обработай ошибку здесь
    return
}
// используй value
```

Это многословнее, но делает код **предсказуемым**: ты всегда видишь, где может возникнуть ошибка.
В Python исключение может прилететь из любого места и «всплыть» неожиданно.

---

### 10. Компиляция и деплой

Python:
```bash
pip install -r requirements.txt
python api.py
# нужен Python на сервере + все зависимости
```

Go:
```bash
go build -o server main.go
./server
# один файл, никаких зависимостей на сервере
```

Это огромное преимущество для деплоя в Docker:

```dockerfile
# Python образ
FROM python:3.12-slim   # ~150 МБ
COPY . .
RUN pip install -r requirements.txt

# Go образ
FROM scratch            # 0 МБ — пустой образ!
COPY server /server
CMD ["/server"]         # итоговый образ ~10 МБ
```

---

## Итог: когда выбирать Go

Выбирай Go, если:
- Строишь API или микросервис с высокой нагрузкой
- Важна предсказуемая производительность
- Нужен простой деплой (один бинарник)
- Команда хочет строгую типизацию и явную обработку ошибок

Оставайся на Python, если:
- Работаешь с ML/Data Science
- Нужен быстрый прототип
- Пишешь скрипты автоматизации
- Экосистема Python критична для задачи

Этот проект — хороший пример: Flask-сервис с SQLite отлично работает на Python.
Но Go-версия того же сервиса запустится быстрее, потребует меньше памяти
и без проблем выдержит в 20 раз больше одновременных запросов.
