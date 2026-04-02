# --- Stage 1: build ---
FROM golang:1.22-alpine AS builder

# gcc нужен для CGO (go-sqlite3)
RUN apk add --no-cache gcc musl-dev

WORKDIR /app

# Копируем всё сразу, затем скачиваем зависимости и собираем
COPY . .
RUN go get github.com/mattn/go-sqlite3@v1.14.22 \
    && go mod tidy \
    && CGO_ENABLED=1 GOOS=linux go build -o server .

# --- Stage 2: minimal runtime ---
FROM alpine:3.19

RUN apk add --no-cache libc6-compat

WORKDIR /app

COPY --from=builder /app/server .

EXPOSE 8080

CMD ["./server"]
