from utils.auth import _fetch_auth_user, available_roles, list_app_users


def normalize_managed_user_form(form):
    username = (form.get("username", "") or "").strip().lower()
    display_name = (form.get("display_name", "") or "").strip() or username
    role = (form.get("role", "tecnico") or "tecnico").strip().lower()
    technician_name = (form.get("technician_name", "") or "").strip()
    phone = (form.get("phone", "") or "").strip()

    return {
        "is_edit_mode": form.get("is_edit_mode") == "1",
        "username": username,
        "display_name": display_name,
        "password": form.get("password", "") or "",
        "is_superuser_flag": form.get("is_superuser") == "on",
        "is_active": form.get("is_active") == "on",
        "must_change_password": form.get("must_change_password") == "on",
        "role": role,
        "technician_name": technician_name,
        "phone": phone,
        "permissions": {
            "dashboard": form.get("perm_dashboard") == "on",
            "mobile": form.get("perm_mobile") == "on",
            "infrastructure": form.get("perm_infrastructure") == "on",
            "reports": form.get("perm_reports") == "on",
            "operadores": form.get("perm_operadores") == "on",
        },
    }


def validate_managed_user_payload(payload):
    username = payload["username"]
    if not username:
        raise ValueError("El usuario es obligatorio.")
    if " " in username:
        raise ValueError("El usuario no debe contener espacios.")
    if payload["role"] not in available_roles():
        raise ValueError("El rol indicado no es válido.")


def hydrate_existing_user_defaults(payload):
    existing_user = _fetch_auth_user(payload["username"])
    payload["existing_user"] = existing_user

    if payload["is_edit_mode"] and existing_user:
        if not payload["display_name"] or payload["display_name"] == payload["username"]:
            payload["display_name"] = existing_user.get("display_name") or payload["display_name"]
        if not payload["technician_name"]:
            payload["technician_name"] = existing_user.get("technician_name") or ""
        if not payload["phone"]:
            payload["phone"] = existing_user.get("phone") or ""

    return payload


def list_pending_users():
    return [row for row in list_app_users() if not row.get("is_active")]
