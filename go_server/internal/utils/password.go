package utils

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
)

// HashPassword возвращает строку вида "hex_salt$hex_hash".
// Использует SHA-256 с 16-байтовой случайной солью.
// Для продакшена рекомендуется golang.org/x/crypto/pbkdf2.
func HashPassword(password string) string {
	saltBytes := make([]byte, 16)
	_, _ = rand.Read(saltBytes)
	salt := hex.EncodeToString(saltBytes)

	h := sha256.New()
	h.Write(saltBytes)
	h.Write([]byte(password))
	hash := hex.EncodeToString(h.Sum(nil))

	return fmt.Sprintf("%s$%s", salt, hash)
}
