package handlers

import (
	"net/http"
	"strconv"

	"go_server/internal/utils"
)

// Activate обрабатывает GET|POST /activate/{uid}.
func Activate(w http.ResponseWriter, r *http.Request) {
	uid, err := strconv.Atoi(r.PathValue("uid"))
	if err != nil {
		utils.WriteJSON(w, http.StatusBadRequest, utils.ErrorResponse{Error: "uid must be an integer"})
		return
	}

	utils.AddActiveUser(uid)
	utils.WriteJSON(w, http.StatusOK, map[string]any{
		"status": "ok",
		"active": utils.GetActiveUsersSnapshot(),
	})
}
