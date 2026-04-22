from utils.auth import current_username


def log_audit_event(
    conn,
    *,
    pc_name,
    field,
    old_value,
    new_value,
    action_type="UPDATE",
    actor=None,
    request_ip=None,
):
    conn.execute(
        """
        INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            pc_name,
            field,
            "" if old_value is None else str(old_value),
            "" if new_value is None else str(new_value),
            actor or current_username() or "SISTEMA",
            action_type,
            request_ip,
        ),
    )
