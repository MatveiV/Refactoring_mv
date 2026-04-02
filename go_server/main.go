package main

import (
	"log"
	"net/http"

	"go_server/internal/db"
	"go_server/internal/handlers"
)

func main() {
	database := db.Open("./users.db")
	defer database.Close()

	mux := http.NewServeMux()

	// Index
	mux.HandleFunc("GET /", handlers.Index)

	// Users
	mux.HandleFunc("POST /adduser", handlers.AddUser(database))
	mux.HandleFunc("GET /user/{uid}", handlers.GetUser(database))

	// Active users
	mux.HandleFunc("GET /activate/{uid}", handlers.Activate)
	mux.HandleFunc("POST /activate/{uid}", handlers.Activate)

	// Misc
	mux.HandleFunc("GET /slow", handlers.Slow)
	mux.HandleFunc("GET /wrong", handlers.Wrong)

	addr := ":8080"
	log.Printf("server listening on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
