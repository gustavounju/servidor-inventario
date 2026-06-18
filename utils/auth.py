import hmac
import os
import secrets
import hashlib
from functools import wraps

from flask import current_app, flash, jsonify, redirect, request, session, url_for


AUTH_SESSION_KEY = "auth_user"
CSRF_SESSION_KEY = "csrf_token"
PASSWORD_SCHEME = "pbkdf2_sha256"

PERMISSION_COLUMN_MAP = {
    "dashboard": "can_access_dashboard",
    "mobile": "can_access_mobile",
    "infrastructure": "can_access_infrastructure",
    "reports": "can_access_reports",
    "operadores": "can_access_operadores",
    "audit_racks": "can_audit_racks",
}

ROLE_PRESETS = {
    "administrador": {
        "dashboard": True,
        "mobile": True,
        "infrastructure": True,
        "reports": True,
        "audit_racks": True,
    },
    "operador": {
        "dashboard": False,
        "mobile": False,
        "infrastructure": False,
        "reports": False,
        "operadores": True,
        "audit_racks": False,
    },
    "tecnico": {
        "dashboard": False,
        "mobile": True,
        "infrastructure": False,
        "reports": False,
        "audit_racks": False,
    },
    "infraestructura": {
        "dashboard": True,
        "mobile": True,
        "infrastructure": True,
        "reports": True,
        "audit_racks": True,
    },
    "consulta": {
        "dashboard": False,
        "mobile": False,
        "infrastructure": False,
        "reports": True,
        "audit_racks": False,
    },
}

MODULE_DEFINITIONS = [
    {
        "key": "dashboard",
        "label": "Dashboard",
        "endpoint": "dashboard.dashboard",
        "icon": "bi-grid-1x2-fill",
        "active_prefixes": ["dashboard."],
    },
    {
        "key": "infrastructure",
        "label": "Infra",
        "endpoint": "infrastructure.index",
        "icon": "bi-hdd-network-fill",
        "active_prefixes": ["infrastructure.", "stock."],
    },
    {
        "key": "reports",
        "label": "Reportes",
        "endpoint": "tasks.report_tasks_completed",
        "icon": "bi-file-earmark-bar-graph-fill",
        "active_prefixes": ["tasks.report_"],
    },
    {
        "key": "mobile",
        "label": "Técnicos",
        "endpoint": "tecnicos.tecnicos_view",
        "icon": "bi-phone-fill",
        "active_prefixes": ["tecnicos.", "mobile."],
    },
    {
        "key": "operadores",
        "label": "Operadores",
        "endpoint": "operadores.operadores_view",
        "icon": "bi-headset",
        "active_prefixes": ["operadores."],
    },
]

PUBLIC_ENDPOINTS = {
    "static",
    "auth.login",
    "auth.logout",
    "auth.pdf_local_tool",
    "auth.local_pdf_ocr",
    "auth.local_pdf_ocr_status",
    "api.receive_inventory",
    "api.health",
    "setup.get_script",
    "setup.install_page",
    "setup.download_client_script",
    "setup.download_client_launcher",
    "setup.download_certificate",
    "auth.change_password",
    "sw.js",
    "manifest.json",
    "tasks.visor",
    "tasks.api_visor_data"
}


def configured_admin_username():
    return os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "administrador")


def configured_admin_password():
    pwd = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")
    if not pwd:
        raise EnvironmentError("BOOTSTRAP_ADMIN_PASSWORD no está definida en el archivo .env.")
    return pwd


def auth_mode():
    mode = os.environ.get("AUTH_MODE", "local").strip().lower()
    if mode not in {"local", "ad", "hybrid"}:
        return "local"
    return mode


def ad_enabled():
    return auth_mode() in {"ad", "hybrid"}


def available_roles():
    return list(ROLE_PRESETS.keys())


def _permissions_from_row(row):
    permissions = {}
    for perm_name, column_name in PERMISSION_COLUMN_MAP.items():
        permissions[perm_name] = bool(row.get(column_name))
    if row.get("is_superuser"):
        for perm_name in permissions:
            permissions[perm_name] = True
    return permissions


def permissions_for_role(role, is_superuser=False):
    role_key = (role or "tecnico").strip().lower()
    preset = dict(ROLE_PRESETS.get(role_key, ROLE_PRESETS["tecnico"]))
    if is_superuser:
        for perm_name in preset:
            preset[perm_name] = True
    return preset


def build_session_user(row, auth_source):
    role = row.get("role") or ("administrador" if row.get("is_superuser") else "tecnico")
    permissions = _permissions_from_row(row)
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row.get("display_name") or row["username"],
        "role": role,
        "technician_name": row.get("technician_name") or "",
        "permissions": permissions,
        "is_superuser": bool(row.get("is_superuser")),
        "must_change_password": bool(row.get("must_change_password")),
        "is_active": bool(row.get("is_active", True)),
        "phone": row.get("phone") or "",
        "auth_source": auth_source,
    }


def is_authenticated():
    return bool(session.get(AUTH_SESSION_KEY))


def current_user():
    return session.get(AUTH_SESSION_KEY) or {}


def current_username():
    return current_user().get("username")


def is_superuser():
    return bool(current_user().get("is_superuser"))


def has_permission(permission_name, user=None):
    user = user or current_user()
    if not user:
        return False
    if user.get("is_superuser"):
        return True
    role_defaults = ROLE_PRESETS.get((user.get("role") or "").strip().lower(), {})
    if role_defaults.get(permission_name):
        return True
    permissions = user.get("permissions") or {}
    return bool(permissions.get(permission_name))


def current_technician_identity(user=None):
    user = user or current_user()
    if not user:
        return ""
    return (user.get("technician_name") or user.get("display_name") or user.get("username") or "").strip()


def auth_mode_label():
    labels = {
        "local": "Local",
        "ad": "Active Directory",
        "hybrid": "Hibrido (AD + local)",
    }
    return labels.get(auth_mode(), "Local")


def role_label(role_name=None):
    labels = {
        "administrador": "Administrador",
        "operador": "Operador",
        "tecnico": "Tecnico",
        "infraestructura": "Infraestructura",
        "consulta": "Consulta",
    }
    role_key = (role_name or current_user().get("role") or "").strip().lower()
    return labels.get(role_key, role_key.capitalize() if role_key else "Sin rol")


def allowed_module_links(user=None):
    user = user or current_user()
    endpoint = request.endpoint or ""
    ua = (request.user_agent.string or "").lower()
    is_mobile_client = any(token in ua for token in ["android", "iphone", "ipad", "mobile"])
    links = []
    for module in MODULE_DEFINITIONS:
        if not has_permission(module["key"], user):
            continue
        # Ocultar el link de Técnicos en escritorio si el usuario tiene acceso al dashboard
        if module["key"] == "mobile" and has_permission("dashboard", user) and not is_mobile_client:
            continue
        # Ocultar links irrelevantes para operadores en su vista simplificada
        if user.get("role") == "operador" and module["key"] in ["infrastructure"]:
            continue
            
        links.append({
            "key": module["key"],
            "label": module["label"],
            "icon": module["icon"],
            "url": url_for(module["endpoint"]),
            "active": any(endpoint.startswith(prefix) for prefix in module["active_prefixes"]),
        })
    return links


def generate_csrf_token():
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_hex(32)
        session[CSRF_SESSION_KEY] = token
    return token


def clear_auth_session():
    session.pop(AUTH_SESSION_KEY, None)
    session.pop(CSRF_SESSION_KEY, None)


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt.encode("utf-8"), 390000)
    return f"{PASSWORD_SCHEME}${salt}${digest.hex()}"


def verify_password(password, stored_hash):
    if not stored_hash:
        return False
    try:
        scheme, salt, digest = stored_hash.split("$", 2)
    except ValueError:
        return False

    if scheme != PASSWORD_SCHEME:
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt.encode("utf-8"), 390000).hex()
    return hmac.compare_digest(candidate, digest)


def _fetch_auth_user(username):
    from database.db_core import get_db_connection

    with get_db_connection() as conn:
        return conn.execute(
            """
            SELECT id, username, display_name, role, technician_name, password_hash,
                   is_superuser, is_active, must_change_password, phone,
                   can_access_dashboard, can_access_mobile, can_access_infrastructure, can_access_reports, can_access_operadores, can_audit_racks
            FROM app_users
            WHERE username = %s
            LIMIT 1
            """,
            (username,),
        ).fetchone()


def _normalize_username(username):
    cleaned = (username or "").strip().lower()
    if "\\" in cleaned:
        cleaned = cleaned.split("\\")[-1]
    if "@" in cleaned:
        cleaned = cleaned.split("@")[0]
    return cleaned


def _ad_superusers():
    raw = os.environ.get("AD_SUPERUSERS", "")
    return {_normalize_username(item) for item in raw.split(",") if item.strip()}


def _ad_default_domain():
    return os.environ.get("AD_DOMAIN", "").strip()


def _build_ad_login_variants(username):
    normalized = _normalize_username(username)
    domain = _ad_default_domain()
    variants = [username, normalized]
    if domain and normalized:
        variants.append(f"{domain}\\{normalized}")
        variants.append(f"{normalized}@{domain}")
    deduped = []
    for item in variants:
        candidate = (item or "").strip()
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return deduped


def _authenticate_against_ad(username, password):
    if not ad_enabled():
        return None

    ad_server = os.environ.get("AD_SERVER", "").strip()
    if not ad_server:
        return None

    try:
        from ldap3 import ALL, NTLM, SIMPLE, Connection, Server
    except Exception as exc:
        current_app.logger.warning("ldap3 no disponible para AD: %s", exc)
        return None

    use_ssl = os.environ.get("AD_USE_SSL", "false").strip().lower() == "true"
    connect_timeout = int(os.environ.get("AD_CONNECT_TIMEOUT", "5"))
    base_dn = os.environ.get("AD_BASE_DN", "").strip()
    server = Server(ad_server, use_ssl=use_ssl, get_info=ALL, connect_timeout=connect_timeout)

    domain = _ad_default_domain()
    normalized = _normalize_username(username)
    # SIMPLE auth funciona con user@domain. Probamos esa variante primero, luego las demás.
    if domain and normalized:
        bind_variants = [f"{normalized}@{domain}", normalized, username]
    else:
        bind_variants = [username, normalized]
    # Deduplicar manteniendo orden
    seen = set()
    bind_variants = [v for v in bind_variants if v and not (v in seen or seen.add(v))]

    for bind_user in bind_variants:
        try:
            from ldap3 import SIMPLE as LDAP_SIMPLE
            conn = Connection(server, user=bind_user, password=password, authentication=LDAP_SIMPLE, auto_bind=True)
            display_name = _normalize_username(username)
            mail = None
            if base_dn:
                search_name = _normalize_username(username)
                if conn.search(base_dn, f"(sAMAccountName={search_name})", attributes=["displayName", "mail", "sAMAccountName"]):
                    if conn.entries:
                        entry = conn.entries[0]
                        display_attr = getattr(entry, "displayName", None)
                        mail_attr = getattr(entry, "mail", None)
                        display_name = str(getattr(display_attr, "value", display_attr) or display_name)
                        mail = str(getattr(mail_attr, "value", mail_attr) or "") or None
            conn.unbind()
            username_normalized = _normalize_username(username)
            return {
                "username": username_normalized,
                "display_name": display_name,
                "auth_source": "ad",
                "is_superuser": username_normalized in _ad_superusers(),
                "must_change_password": False,
                "email": mail,
            }
        except Exception:
            continue

    return None


def _ensure_ad_shadow_user(ad_user):
    from database.db_core import get_db_connection

    username = _normalize_username(ad_user.get("username"))
    display_name = ad_user.get("display_name") or username
    superuser_flag = 1 if ad_user.get("is_superuser") else 0
    # Los AD_SUPERUSERS se activan siempre. Otros dependen de la configuración (por defecto requieren aprobación)
    auto_activate = superuser_flag or os.environ.get("AD_AUTO_APPROVE", "false").lower() == "true"

    with get_db_connection() as conn:
        existing = conn.execute(
            """
            SELECT id, username, display_name, role, technician_name, password_hash,
                   is_superuser, is_active, must_change_password, phone,
                   can_access_dashboard, can_access_mobile, can_access_infrastructure, can_access_reports, can_access_operadores, can_audit_racks
            FROM app_users WHERE username = %s LIMIT 1
            """,
            (username,),
        ).fetchone()
        if existing:
            # Si el usuario ya existe, actualizamos su info básica pero NO tocamos is_active 
            # (a menos que sea para activarlo si es superuser y estaba inactivo)
            new_active_status = existing["is_active"]
            if superuser_flag:
                new_active_status = 1

            conn.execute(
                """
                UPDATE app_users
                SET display_name = %s,
                    is_superuser = %s,
                    is_active = %s,
                    phone = COALESCE(phone, %s),
                    updated_at = CURRENT_TIMESTAMP
                WHERE username = %s
                """,
                (display_name, superuser_flag, new_active_status, ad_user.get("phone"), username),
            )
            conn.commit()
            existing["display_name"] = display_name
            existing["is_superuser"] = superuser_flag
            existing["is_active"] = new_active_status
            return build_session_user(existing, "ad")

        generated_hash = hash_password(secrets.token_urlsafe(32))
        default_permissions = permissions_for_role("tecnico", is_superuser=bool(superuser_flag))
        
        # REGLA SEGURIDAD: Nuevos usuarios AD nacen INACTIVOS (Pendientes de aprobación)
        # excepto si están en la lista de AD_SUPERUSERS o si AD_AUTO_APPROVE=true
        is_active_flag = 1 if auto_activate else 0
        
        cursor = conn.execute(
            """
            INSERT INTO app_users (
                username, display_name, role, technician_name, password_hash,
                is_superuser, is_active, must_change_password, phone,
                can_access_dashboard, can_access_mobile, can_access_infrastructure, can_access_reports, can_access_operadores, can_audit_racks
            )
            VALUES (%s, %s, %s, NULL, %s, %s, %s, 0, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                username,
                display_name,
                "administrador" if superuser_flag else "tecnico",
                generated_hash,
                superuser_flag,
                is_active_flag,
                ad_user.get("phone"),
                1 if default_permissions["dashboard"] else 0,
                1 if default_permissions["mobile"] else 0,
                1 if default_permissions["infrastructure"] else 0,
                1 if default_permissions["reports"] else 0,
                1 if default_permissions.get("operadores") else 0,
                1 if default_permissions.get("audit_racks") else 0,
            ),
        )
        conn.commit()
        return build_session_user(
            {
                "id": cursor.lastrowid,
                "username": username,
                "display_name": display_name,
                "role": "administrador" if superuser_flag else "tecnico",
                "technician_name": "",
                "is_superuser": superuser_flag,
                "is_active": is_active_flag,
                "must_change_password": False,
                "can_access_dashboard": default_permissions["dashboard"],
                "can_access_mobile": default_permissions["mobile"],
                "can_access_infrastructure": default_permissions["infrastructure"],
                "can_access_reports": default_permissions["reports"],
                "can_access_operadores": default_permissions.get("operadores", False),
                "can_audit_racks": default_permissions.get("audit_racks", False),
                "phone": ad_user.get("phone") or "",
            },
            "ad",
        )



def validate_login(username_raw, password):
    username = _normalize_username(username_raw)
    mode = auth_mode()

    # REGLA SEGURIDAD: Bloquear cuentas que terminen en _adm (deben usar la normal)
    if username.strip().lower().endswith("_adm"):
        flash("Por seguridad, no se permite el ingreso con cuentas administrativas (_adm). Por favor usa tu cuenta de AD común.", "error")
        return None

    if mode in {"local", "hybrid"}:
        user = _fetch_auth_user(username)
        # Verificamos la clave primero. Si coincide, retornamos el usuario 
        # independientemente de si está activo o no, para que el login pueda
        # mostrar el mensaje de "pendiente de aprobación".
        if user and verify_password(password, user.get("password_hash")):
            return build_session_user(user, "local")

    if mode in {"ad", "hybrid"}:
        ad_user = _authenticate_against_ad(username, password)
        if ad_user:
            return _ensure_ad_shadow_user(ad_user)

    return None



def count_superusers(exclude_username=None):
    from database.db_core import get_db_connection

    sql = "SELECT COUNT(*) AS c FROM app_users WHERE is_superuser = 1 AND is_active = 1"
    params = []
    if exclude_username:
        sql += " AND username != %s"
        params.append(exclude_username)
    with get_db_connection() as conn:
        return conn.execute(sql, params).fetchone()["c"]


def list_app_users():
    from database.db_core import get_db_connection

    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT au.id, au.username, au.display_name, au.role, au.technician_name, au.is_superuser, au.is_active,
                   au.must_change_password, au.phone, au.can_access_dashboard, au.can_access_mobile,
                   au.can_access_infrastructure, au.can_access_reports, au.can_access_operadores, au.can_audit_racks, au.created_at, au.updated_at,
                   CASE WHEN ad.username IS NULL THEN 0 ELSE 1 END AS is_ad_user
            FROM app_users au
            LEFT JOIN ad_users ad ON LOWER(ad.username) = LOWER(au.username)
            ORDER BY au.is_superuser DESC, au.username ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def list_technician_users():
    users = []
    seen = set()
    for row in list_app_users():
        if not row.get("is_active"):
            continue
        
        # Omitir específicamente el usuario genérico 'administrador'
        if row.get("username") == "administrador":
            continue

        role = (row.get("role") or "").strip().lower()
        if role in {"consulta", "operador"}:
            continue

        explicit_mobile_identity = bool((row.get("technician_name") or "").strip())
        
        # Permitir administradores y otros roles con acceso móvil
        # Eliminamos la restricción que obligaba a tener technician_name para superusuarios
        if not (row.get("can_access_mobile") or explicit_mobile_identity or role in {"tecnico", "infraestructura", "administrador"}):
            continue

        display = (row.get("technician_name") or row.get("display_name") or row.get("username") or "").strip()
        if not display:
            continue
        key = display.lower()
        if key in seen:
            continue
        seen.add(key)
        users.append({
            "name": display,
            "username": row.get("username"),
            "display_name": row.get("display_name") or display,
            "role": row.get("role") or "tecnico",
        })

    users.sort(key=lambda item: item["name"].lower())
    return users


def upsert_app_user(username, password, display_name=None, is_superuser_flag=False, is_active=True, must_change_password=False, role="tecnico", technician_name=None, permissions=None, phone=None):
    from database.db_core import get_db_connection

    username = (username or "").strip().lower()
    if not username:
        raise ValueError("El usuario es obligatorio")

    role = (role or "tecnico").strip().lower()
    display_name = (display_name or username).strip()
    if not technician_name and role in {"tecnico", "infraestructura"}:
        technician_name = display_name
    effective_permissions = permissions_for_role(role, is_superuser=is_superuser_flag)
    if permissions:
        for perm_name in effective_permissions:
            if perm_name in permissions:
                effective_permissions[perm_name] = bool(permissions[perm_name])
    if is_superuser_flag:
        for perm_name in effective_permissions:
            effective_permissions[perm_name] = True

    with get_db_connection() as conn:
        existing = conn.execute("SELECT password_hash FROM app_users WHERE username = %s LIMIT 1", (username,)).fetchone()
        if password:
            password_hash = hash_password(password)
        elif existing and existing.get("password_hash"):
            password_hash = existing["password_hash"]
        else:
            raise ValueError("La clave es obligatoria para usuarios nuevos")

        conn.execute(
            """
            INSERT INTO app_users (
                username, display_name, role, technician_name, password_hash,
                is_superuser, is_active, must_change_password, phone,
                can_access_dashboard, can_access_mobile, can_access_infrastructure, can_access_reports, can_access_operadores, can_audit_racks
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                display_name = VALUES(display_name),
                role = VALUES(role),
                technician_name = VALUES(technician_name),
                password_hash = VALUES(password_hash),
                is_superuser = VALUES(is_superuser),
                is_active = VALUES(is_active),
                must_change_password = VALUES(must_change_password),
                can_access_dashboard = VALUES(can_access_dashboard),
                can_access_mobile = VALUES(can_access_mobile),
                can_access_infrastructure = VALUES(can_access_infrastructure),
                can_access_reports = VALUES(can_access_reports),
                can_access_operadores = VALUES(can_access_operadores),
                can_audit_racks = VALUES(can_audit_racks),
                phone = VALUES(phone),
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                username,
                display_name,
                role,
                (technician_name or "").strip() or None,
                password_hash,
                1 if is_superuser_flag else 0,
                1 if is_active else 0,
                1 if must_change_password else 0,
                phone,
                1 if effective_permissions["dashboard"] else 0,
                1 if effective_permissions["mobile"] else 0,
                1 if effective_permissions["infrastructure"] else 0,
                1 if effective_permissions["reports"] else 0,
                1 if effective_permissions.get("operadores") else 0,
                1 if effective_permissions.get("audit_racks") else 0,
            ),
        )
        conn.commit()


def update_app_user_password(username, new_password):
    from database.db_core import get_db_connection
    username = (username or "").strip().lower()
    if not username or not new_password:
        raise ValueError("Usuario y nueva clave son obligatorios")
    
    password_hash = hash_password(new_password)
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE app_users SET password_hash = %s, must_change_password = 0, updated_at = CURRENT_TIMESTAMP WHERE username = %s",
            (password_hash, username)
        )
        conn.commit()


def ensure_default_admin():
    from database.db_core import get_db_connection

    with get_db_connection() as conn:
        total_users = conn.execute("SELECT COUNT(*) AS c FROM app_users").fetchone()["c"]
    if total_users > 0:
        return False

    upsert_app_user(
        configured_admin_username(),
        configured_admin_password(),
        display_name="Administrador Inicial",
        is_superuser_flag=True,
        is_active=True,
        must_change_password=True,
        role="administrador",
    )
    return True


def delete_app_user(user_id, acting_username=None):
    from database.db_core import get_db_connection

    with get_db_connection() as conn:
        user = conn.execute("SELECT username, is_superuser FROM app_users WHERE id = %s", (user_id,)).fetchone()
        if not user:
            raise ValueError("Usuario no encontrado")
        if acting_username and user["username"] == acting_username:
            raise ValueError("No puedes eliminar tu propio usuario desde la sesion actual")
        if user.get("is_superuser") and count_superusers(exclude_username=user["username"]) == 0:
            raise ValueError("Debe quedar al menos un superusuario activo")
        conn.execute("DELETE FROM app_users WHERE id = %s", (user_id,))
        conn.commit()


def refresh_session_user():
    username = current_username()
    auth_source = current_user().get("auth_source") or "local"
    if not username:
        return None

    import time
    now = time.time()
    last_refresh = session.get("last_auth_refresh", 0)

    # REGLA DE RENDIMIENTO: Evitar asediar la BD en cada click. 
    # Solo re-validamos si el usuario sigue activo cada 60 segundos.
    if (now - last_refresh) < 60:
        return session.get(AUTH_SESSION_KEY)

    user = _fetch_auth_user(username)
    if not user or not user.get("is_active"):
        clear_auth_session()
        return None
        
    session["last_auth_refresh"] = now
    session[AUTH_SESSION_KEY] = build_session_user(user, auth_source)
    return session[AUTH_SESSION_KEY]


def required_permission_for_endpoint(endpoint=None):
    endpoint = endpoint or request.endpoint or ""
    if endpoint.startswith("mobile.") or endpoint.startswith("tecnicos."):
        return "mobile"
    if endpoint.startswith("operadores."):
        return "operadores"

    mobile_allowed_stock_endpoints = {
        "stock.get_component", 
        "stock.add_component", 
        "stock.assign_component", 
        "stock.return_component",
        "stock.list_suppliers",
        "tasks.get_task_actions",
        "tasks.add_task_action"
    }
    if endpoint in mobile_allowed_stock_endpoints:
        return "mobile"

    if endpoint.startswith("stock.") or endpoint.startswith("infrastructure."):
        return "infrastructure"
    if endpoint in {"tasks.report_tasks_completed", "tasks.report_tasks_completed_pdf", "tasks.report_preview"}:
        return "reports"
    if endpoint.startswith("tasks."):
        return "dashboard"
    if endpoint.startswith("dashboard."):
        return "dashboard"
    return None


def forbidden_response(permission_name):
    if request.path.startswith("/api/") or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "error", "message": f"Sin permiso para {permission_name}"}), 403

    flash(f"Tu usuario no tiene permiso para entrar en '{permission_name}'.", "error")
    return redirect(default_landing_url())


def default_landing_url(user=None):
    user = user or current_user()
    if not user:
        return url_for("dashboard.dashboard")
    ua = (request.user_agent.string or "").lower()
    is_mobile_client = any(token in ua for token in ["android", "iphone", "ipad", "mobile"])

    # Redirección específica para Operadores Telefónicos
    if user.get("role") == "operador":
        return url_for("operadores.operadores_view")

    if is_mobile_client and has_permission("mobile", user):
        return url_for("tecnicos.tecnicos_view")

    if has_permission("dashboard", user):
        return url_for("dashboard.dashboard")
    if has_permission("infrastructure", user):
        return url_for("infrastructure.index")
    if has_permission("reports", user):
        return url_for("tasks.report_tasks_completed")
    if has_permission("mobile", user):
        return url_for("tecnicos.tecnicos_view")
    return url_for("auth.logout")


def has_valid_api_token():
    expected = os.environ.get("INVENTARIO_API_TOKEN", "").strip()
    if not expected:
        return False

    bearer = request.headers.get("Authorization", "")
    header_token = request.headers.get("X-API-Key", "")
    candidate = header_token.strip()
    if bearer.lower().startswith("bearer "):
        candidate = bearer[7:].strip()

    return bool(candidate) and hmac.compare_digest(candidate, expected)


def is_public_endpoint(endpoint=None):
    endpoint = endpoint or request.endpoint
    return endpoint in PUBLIC_ENDPOINTS


def should_enforce_auth(endpoint=None):
    endpoint = endpoint or request.endpoint
    if not endpoint:
        return False
    return not is_public_endpoint(endpoint)


def unauthorized_response():
    if request.path.startswith("/api/") or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "error", "message": "No autenticado"}), 401
    return redirect(url_for("auth.login", next=request.full_path if request.query_string else request.path))


def auth_guard():
    if not should_enforce_auth():
        return None

    if has_valid_api_token():
        return None

    if not is_authenticated():
        return unauthorized_response()

    refreshed_user = refresh_session_user()
    if not refreshed_user:
        return unauthorized_response()

    # SI EL USUARIO DEBE CAMBIAR LA CLAVE, LO FORZAMOS
    if refreshed_user.get("must_change_password") and request.endpoint != "auth.change_password":
        # Avisar al usuario por qué está aquí si es redireccionado
        return redirect(url_for("auth.change_password"))

    # --- REGLA DE ACCESO MÓVIL (Fuerza /tecnicos en celulares) ---
    ua = (request.user_agent.string or "").lower()
    is_mobile_client = any(token in ua for token in ["android", "iphone", "ipad", "mobile"])
    
    if is_mobile_client and not (request.path.startswith("/api/") or request.headers.get("X-Requested-With") == "XMLHttpRequest"):
        permission_name = required_permission_for_endpoint()
        # Si estamos en móvil, permitimos las experiencias diseñadas para celular.
        # o endpoints públicos (que ya pasaron el primer filtro de should_enforce_auth).
        if permission_name not in {"mobile", "operadores"}:
            if refreshed_user.get("role") == "operador":
                return redirect(url_for("operadores.operadores_view"))
            # Si tiene permiso de móvil, lo mandamos allá. Si no, login/logout manejarán el resto.
            if refreshed_user.get("can_access_mobile") or refreshed_user.get("is_superuser"):
                return redirect(url_for("tecnicos.tecnicos_view"))
    # -------------------------------------------------------------

    permission_name = required_permission_for_endpoint()
    operator_mobile_bridge_endpoints = {
        "mobile.voice_upload",
        "mobile.api_mobile_parse_voice",
    }
    if (
        refreshed_user.get("role") == "operador"
        and request.endpoint in operator_mobile_bridge_endpoints
    ):
        permission_name = "operadores"

    if permission_name and not has_permission(permission_name, refreshed_user):
        return forbidden_response(permission_name)

    return None


def csrf_guard():
    if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
        return None

    if is_public_endpoint():
        return None

    if has_valid_api_token():
        return None

    token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    session_token = session.get(CSRF_SESSION_KEY)
    if not token or not session_token or not hmac.compare_digest(token, session_token):
        current_app.logger.warning("CSRF token invalido para %s", request.path)
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "CSRF token invalido"}), 400
        return "CSRF token invalido", 400

    return None


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if has_valid_api_token():
            return view_func(*args, **kwargs)
        if is_authenticated() and refresh_session_user():
            return view_func(*args, **kwargs)
        return unauthorized_response()

    return wrapped


def superuser_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if is_authenticated() and refresh_session_user() and is_superuser():
            return view_func(*args, **kwargs)
        return redirect(url_for("dashboard.dashboard"))

    return wrapped


def permission_required(permission_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if has_valid_api_token():
                return view_func(*args, **kwargs)
            if not is_authenticated():
                return unauthorized_response()
            refreshed_user = refresh_session_user()
            if refreshed_user and has_permission(permission_name, refreshed_user):
                return view_func(*args, **kwargs)
            return forbidden_response(permission_name)

        return wrapped

    return decorator
