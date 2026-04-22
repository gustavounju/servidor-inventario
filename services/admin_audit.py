import json


def log_admin_event(conn, *, action_type, actor_username, target_username, ip_address=None, details=None):
    """Registra auditoría de acciones administrativas sobre usuarios."""
    conn.execute(
        """
        INSERT INTO admin_audit_logs (
            action_type,
            actor_username,
            target_username,
            ip_address,
            details
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            (action_type or "").strip() or "UNKNOWN",
            (actor_username or "").strip() or "SISTEMA",
            (target_username or "").strip() or "",
            (ip_address or "").strip() or None,
            json.dumps(details or {}, ensure_ascii=True),
        ),
    )
