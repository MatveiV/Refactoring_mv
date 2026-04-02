package models

// User представляет запись пользователя из базы данных.
type User struct {
	ID   int64  `json:"id"`
	Name string `json:"name"`
}

// AddUserRequest — тело POST /adduser.
type AddUserRequest struct {
	Name string `json:"name"`
}

// AddUserResponse — ответ на успешное создание пользователя.
type AddUserResponse struct {
	Status string `json:"status"`
	ID     int64  `json:"id"`
	Name   string `json:"name"`
}
