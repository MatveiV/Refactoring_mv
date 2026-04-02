package handlers

import (
	"log"
	"net/http"
	"time"

	"go_server/internal/utils"
)

// Index обрабатывает GET / — возвращает HTML-страницу с описанием API.
func Index(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>User Service API</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 40px 20px; }
    .container { max-width: 800px; margin: 0 auto; }
    h1 { font-size: 2rem; font-weight: 700; color: #38bdf8; margin-bottom: 8px; }
    .subtitle { color: #94a3b8; margin-bottom: 40px; font-size: 1rem; }
    .badge { display: inline-block; background: #1e3a5f; color: #38bdf8;
             font-size: 0.75rem; padding: 2px 10px; border-radius: 999px;
             margin-bottom: 32px; }
    .endpoint { background: #1e293b; border: 1px solid #334155;
                border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; }
    .endpoint-header { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
    .method { font-weight: 700; font-size: 0.8rem; padding: 3px 10px;
              border-radius: 6px; min-width: 60px; text-align: center; }
    .get  { background: #064e3b; color: #34d399; }
    .post { background: #1e3a5f; color: #60a5fa; }
    .path { font-family: monospace; font-size: 1rem; color: #f1f5f9; }
    .desc { color: #94a3b8; font-size: 0.9rem; margin-bottom: 10px; }
    .example { background: #0f172a; border-radius: 8px; padding: 12px 16px;
               font-family: monospace; font-size: 0.85rem; color: #86efac;
               overflow-x: auto; }
    .example span { color: #94a3b8; }
    h2 { font-size: 1.1rem; color: #94a3b8; margin: 32px 0 16px;
         text-transform: uppercase; letter-spacing: 0.05em; }
    footer { margin-top: 48px; color: #475569; font-size: 0.85rem; text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <h1>User Service API</h1>
    <p class="subtitle">REST API для управления пользователями</p>
    <span class="badge">Go · SQLite · порт 8080</span>

    <h2>Эндпоинты</h2>

    <div class="endpoint">
      <div class="endpoint-header">
        <span class="method post">POST</span>
        <span class="path">/adduser</span>
      </div>
      <p class="desc">Создать нового пользователя. Тело запроса — JSON с полем <code>name</code>.</p>
      <div class="example">
        <span>Запрос:</span>  curl -X POST http://localhost:8080/adduser \<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-H "Content-Type: application/json" \<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-d '{"name":"Alice"}'<br><br>
        <span>Ответ 201:</span> {"status":"ok","id":1,"name":"Alice"}
      </div>
    </div>

    <div class="endpoint">
      <div class="endpoint-header">
        <span class="method get">GET</span>
        <span class="path">/user/{id}</span>
      </div>
      <p class="desc">Получить пользователя по числовому ID.</p>
      <div class="example">
        <span>Запрос:</span>  curl http://localhost:8080/user/1<br><br>
        <span>Ответ 200:</span> {"id":1,"name":"Alice"}<br>
        <span>Ответ 404:</span> {"error":"not_found"}
      </div>
    </div>

    <div class="endpoint">
      <div class="endpoint-header">
        <span class="method get">GET</span>
        <span class="path">/activate/{id}</span>
      </div>
      <p class="desc">Активировать пользователя. Хранит последние 5 активных ID (in-memory, потокобезопасно).</p>
      <div class="example">
        <span>Запрос:</span>  curl http://localhost:8080/activate/1<br><br>
        <span>Ответ 200:</span> {"status":"ok","active":[1]}
      </div>
    </div>

    <div class="endpoint">
      <div class="endpoint-header">
        <span class="method get">GET</span>
        <span class="path">/slow</span>
      </div>
      <p class="desc">Запускает тяжёлую задачу в горутине (5 сек) и сразу возвращает ответ, не блокируя сервер.</p>
      <div class="example">
        <span>Запрос:</span>  curl http://localhost:8080/slow<br><br>
        <span>Ответ 202:</span> {"status":"scheduled"}
      </div>
    </div>

    <div class="endpoint">
      <div class="endpoint-header">
        <span class="method get">GET</span>
        <span class="path">/wrong</span>
      </div>
      <p class="desc">Демонстрирует корректную обработку ошибок — возвращает JSON вместо пустого тела.</p>
      <div class="example">
        <span>Запрос:</span>  curl http://localhost:8080/wrong<br><br>
        <span>Ответ 500:</span> {"msg":"error","detail":"division by zero"}
      </div>
    </div>

    <footer>User Service · Go 1.22 · <a href="https://hub.docker.com/r/matveiv25/refactoring_mv" style="color:#38bdf8">Docker Hub</a></footer>
  </div>
</body>
</html>`))
}

// Slow обрабатывает GET /slow — запускает задачу в горутине, сразу отвечает 202.
func Slow(w http.ResponseWriter, r *http.Request) {
	go func() {
		time.Sleep(5 * time.Second)
		log.Println("slow task completed")
	}()
	utils.WriteJSON(w, http.StatusAccepted, map[string]string{"status": "scheduled"})
}

// Wrong обрабатывает GET /wrong — демонстрирует корректный JSON-ответ при ошибке.
func Wrong(w http.ResponseWriter, r *http.Request) {
	utils.WriteJSON(w, http.StatusInternalServerError, map[string]string{
		"msg":    "error",
		"detail": "division by zero",
	})
}
