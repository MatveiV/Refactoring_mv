package db

import (
	"database/sql"
	"log"

	_ "github.com/mattn/go-sqlite3"
)

// Open открывает соединение с SQLite и создаёт таблицу users.
func Open(path string) *sql.DB {
	conn, err := sql.Open("sqlite3", path)
	if err != nil {
		log.Fatalf("db: failed to open %s: %v", path, err)
	}

	if err = migrate(conn); err != nil {
		log.Fatalf("db: migration failed: %v", err)
	}

	return conn
}

func migrate(conn *sql.DB) error {
	_, err := conn.Exec(`
		CREATE TABLE IF NOT EXISTS users (
			id   INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL
		)
	`)
	return err
}
