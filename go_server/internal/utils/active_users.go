package utils

import "sync"

const MaxActiveUsers = 5

var (
	activeUsers []int
	activeMu    sync.Mutex
)

// AddActiveUser потокобезопасно добавляет uid в список активных.
// Хранит не более MaxActiveUsers последних записей.
func AddActiveUser(uid int) {
	activeMu.Lock()
	defer activeMu.Unlock()
	activeUsers = append(activeUsers, uid)
	if excess := len(activeUsers) - MaxActiveUsers; excess > 0 {
		activeUsers = activeUsers[excess:]
	}
}

// GetActiveUsersSnapshot возвращает копию списка активных пользователей.
func GetActiveUsersSnapshot() []int {
	activeMu.Lock()
	defer activeMu.Unlock()
	snapshot := make([]int, len(activeUsers))
	copy(snapshot, activeUsers)
	return snapshot
}
