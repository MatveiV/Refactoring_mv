# Полный гайд: Docker Hub → сервер

---

## Часть 1: Локально (твой Windows)

Образы уже запушены, но на случай если нужно повторить:

### 1.1 Логин в Docker Hub

```powershell
docker login
# вводишь логин: matveiv25
# вводишь пароль
```

### 1.2 Пересобрать и запушить образы

```powershell
# Go-сервер
docker build -t matveiv25/refactoring_mv:go-server ./go_server
docker push matveiv25/refactoring_mv:go-server

# Flask API
docker build -f Dockerfile.python -t matveiv25/refactoring_mv:python-api .
docker push matveiv25/refactoring_mv:python-api
```

### 1.3 Проверить на Docker Hub

Открой браузер: `https://hub.docker.com/r/matveiv25/refactoring_mv/tags`

Должны быть два тега: `go-server` и `python-api`.

---

## Часть 2: На сервере (Linux VPS/Ubuntu)

### 2.1 Подключиться к серверу

```bash
ssh user@your-server-ip
# например:
ssh root@185.100.200.50
```

### 2.2 Установить Docker (если не установлен)

```bash
# Обновить пакеты
sudo apt update && sudo apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com | sh

# Добавить пользователя в группу docker (чтобы не писать sudo)
sudo usermod -aG docker $USER

# Применить изменения (или перелогиниться)
newgrp docker

# Проверить
docker --version
```

### 2.3 Установить Docker Compose

```bash
sudo apt install docker-compose-plugin -y

# Проверить
docker compose version
```

### 2.4 Создать папку проекта на сервере

```bash
mkdir ~/refactoring && cd ~/refactoring
```

### 2.5 Создать docker-compose.yml на сервере

```bash
nano docker-compose.yml
```

Вставить содержимое (Ctrl+Shift+V в терминале):

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

Сохранить: `Ctrl+O` → `Enter` → `Ctrl+X`

### 2.6 Скачать образы с Docker Hub и запустить

```bash
# Скачать образы
docker pull matveiv25/refactoring_mv:go-server
docker pull matveiv25/refactoring_mv:python-api

# Запустить оба сервиса в фоне
docker compose up -d
```

### 2.7 Проверить что всё работает

```bash
# Посмотреть статус контейнеров
docker compose ps

# Логи Go-сервера
docker compose logs go-api

# Логи Flask-сервера
docker compose logs python-api

# Быстрая проверка эндпоинтов
curl http://localhost:8080/wrong
curl http://localhost:5000/wrong
```

---

## Часть 3: Открыть порты в файрволе (если нужно)

```bash
# UFW (Ubuntu)
sudo ufw allow 8080/tcp
sudo ufw allow 5000/tcp
sudo ufw status

# или iptables
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

После этого API доступны снаружи:
- Go:    `http://your-server-ip:8080`
- Flask: `http://your-server-ip:5000`

---

## Часть 4: Запустить тесты с локальной машины против сервера

На своём Windows:

```powershell
# Открой test_endpoints.py и поменяй BASE_URL
# BASE_URL = "http://your-server-ip:8080"

python test_endpoints.py
```

---

## Полезные команды на сервере

```bash
# Остановить всё
docker compose down

# Перезапустить
docker compose restart

# Обновить образы (после нового push)
docker compose pull
docker compose up -d

# Посмотреть все контейнеры
docker ps

# Зайти внутрь контейнера
docker exec -it demo-go-api sh
```

---

## Схема процесса

```
Твой Windows                Docker Hub                  Сервер (Linux)
─────────────               ──────────                  ──────────────
docker build  ──push──►  matveiv25/refactoring_mv  ◄──pull──  docker compose up
                            :go-server                          └─ go-api  :8080
                            :python-api                         └─ python-api :5000
```
