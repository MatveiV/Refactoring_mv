# Как зайти на сервер и запустить проект

---

## Шаг 1: Подключиться к серверу по SSH

### Windows (PowerShell или CMD)
```powershell
ssh root@your-server-ip
# например:
ssh root@185.100.200.50
```

### Если используешь SSH-ключ
```powershell
ssh -i C:\Users\ИмяПользователя\.ssh\id_rsa root@185.100.200.50
```

### Если используешь пароль
После ввода команды терминал спросит пароль — вводишь и нажимаешь Enter.

---

## Шаг 2: Установить Docker на сервере (один раз)

```bash
# Обновить список пакетов
sudo apt update && sudo apt upgrade -y

# Установить Docker одной командой
curl -fsSL https://get.docker.com | sh

# Добавить текущего пользователя в группу docker
sudo usermod -aG docker $USER

# Применить изменения без перелогина
newgrp docker

# Проверить установку
docker --version
# Ожидаемый вывод: Docker version 24.x.x, build ...
```

---

## Шаг 3: Установить Docker Compose

```bash
sudo apt install docker-compose-plugin -y

# Проверить
docker compose version
# Ожидаемый вывод: Docker Compose version v2.x.x
```

---

## Шаг 4: Создать папку и файл конфигурации

```bash
# Создать папку проекта
mkdir ~/refactoring && cd ~/refactoring

# Создать docker-compose.yml
nano docker-compose.yml
```

Вставить в редактор следующий текст (Ctrl+Shift+V):

```yaml
services:

  python-api:
    image: matveiv25/refactoring_mv:python-api
    container_name: demo-python-api
    ports:
      - "5000:5000"
    volumes:
      - python-db:/app
    restart: unless-stopped

  go-api:
    image: matveiv25/refactoring_mv:go-server
    container_name: demo-go-api
    ports:
      - "8080:8080"
    volumes:
      - go-db:/app
    restart: unless-stopped

volumes:
  python-db:
  go-db:
```

Сохранить файл: `Ctrl+O` → `Enter` → выйти: `Ctrl+X`

---

## Шаг 5: Скачать образы с Docker Hub и запустить

```bash
# Скачать образы
docker pull matveiv25/refactoring_mv:go-server
docker pull matveiv25/refactoring_mv:python-api

# Запустить оба контейнера в фоновом режиме
docker compose up -d
```

---

## Шаг 6: Проверить что всё работает

```bash
# Посмотреть статус контейнеров (оба должны быть Up)
docker compose ps

# Проверить Go-сервер
curl http://localhost:8080/wrong
# Ожидаемый ответ: {"detail":"division by zero","msg":"error"}

# Проверить Flask-сервер
curl http://localhost:5000/wrong
# Ожидаемый ответ: {"detail":"division by zero","msg":"error"}

# Посмотреть логи Go-сервера
docker compose logs go-api

# Посмотреть логи Flask-сервера
docker compose logs python-api
```

---

## Шаг 7: Открыть порты в файрволе

```bash
# Разрешить входящие подключения на порты 8080 и 5000
sudo ufw allow 8080/tcp
sudo ufw allow 5000/tcp

# Включить файрвол (если не включён)
sudo ufw enable

# Проверить статус
sudo ufw status
```

После этого API доступны из интернета:
- Go API:    `http://your-server-ip:8080`
- Flask API: `http://your-server-ip:5000`

---

## Полезные команды для управления

```bash
# Остановить все контейнеры
docker compose down

# Перезапустить контейнеры
docker compose restart

# Обновить образы до последней версии
docker compose pull
docker compose up -d

# Посмотреть все запущенные контейнеры
docker ps

# Зайти внутрь Go-контейнера
docker exec -it demo-go-api sh

# Зайти внутрь Flask-контейнера
docker exec -it demo-python-api bash
```

---

## Доступные эндпоинты API

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/adduser` | Создать пользователя `{"name": "Alice"}` |
| GET | `/user/{id}` | Получить пользователя по ID |
| GET | `/activate/{id}` | Активировать пользователя |
| GET | `/slow` | Запустить фоновую задачу |
| GET | `/wrong` | Демонстрация обработки ошибок |

---

## Схема

```
Твой компьютер          Docker Hub                    Сервер
──────────────          ──────────                    ──────
docker push  ──────►  matveiv25/refactoring_mv  ◄──pull──  docker compose up -d
                        :go-server                           └─ go-api   → :8080
                        :python-api                          └─ python-api → :5000
```
