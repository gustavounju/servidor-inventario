-- Suscripciones Web Push por técnico/dispositivo.
-- El endpoint completo no se expone en APIs; endpoint_hash evita duplicados.
CREATE TABLE IF NOT EXISTS web_push_subscriptions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    technician_name VARCHAR(255) NOT NULL,
    endpoint TEXT NOT NULL,
    endpoint_hash CHAR(64) NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    user_agent VARCHAR(255) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_web_push_endpoint_hash (endpoint_hash),
    KEY idx_web_push_technician (technician_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
