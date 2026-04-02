package utils

import (
	"encoding/json"
	"net/http"
)

// WriteJSON сериализует payload в JSON и отправляет ответ с заданным статусом.
func WriteJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

// ErrorResponse — стандартный формат ошибки.
type ErrorResponse struct {
	Error string `json:"error"`
}
