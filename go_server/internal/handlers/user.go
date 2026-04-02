package handlers

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"strconv"

	"go_server/internal/models"
	"go_server/internal/utils"
)

// AddUser обрабатывает POST /adduser.
func AddUser(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req models.AddUserRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Name == "" {
			utils.WriteJSON(w, http.StatusBadRequest, utils.ErrorResponse{
				Error: "name is required and must be a non-empty string",
			})
			return
		}

		res, err := db.Exec("INSERT INTO users (name) VALUES (?)", req.Name)
		if err != nil {
			utils.WriteJSON(w, http.StatusInternalServerError, utils.ErrorResponse{Error: "db error"})
			return
		}

		id, _ := res.LastInsertId()
		utils.WriteJSON(w, http.StatusCreated, models.AddUserResponse{
			Status: "ok",
			ID:     id,
			Name:   req.Name,
		})
	}
}

// GetUser обрабатывает GET /user/{uid}.
func GetUser(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		uid, err := strconv.Atoi(r.PathValue("uid"))
		if err != nil {
			utils.WriteJSON(w, http.StatusBadRequest, utils.ErrorResponse{Error: "uid must be an integer"})
			return
		}

		var user models.User
		err = db.QueryRow("SELECT id, name FROM users WHERE id = ?", uid).
			Scan(&user.ID, &user.Name)

		if err == sql.ErrNoRows {
			utils.WriteJSON(w, http.StatusNotFound, utils.ErrorResponse{Error: "not_found"})
			return
		}
		if err != nil {
			utils.WriteJSON(w, http.StatusInternalServerError, utils.ErrorResponse{Error: "db error"})
			return
		}

		utils.WriteJSON(w, http.StatusOK, user)
	}
}
