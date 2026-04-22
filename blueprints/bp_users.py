from flask import Blueprint, flash, redirect, render_template, request, url_for

from database.db_core import get_db_connection
from services.admin_audit import log_admin_event
from services.user_admin import (
    hydrate_existing_user_defaults,
    list_pending_users,
    normalize_managed_user_form,
    validate_managed_user_payload,
)
from utils.auth import (
    _fetch_auth_user,
    current_username,
    delete_app_user,
    list_app_users,
    superuser_required,
    update_app_user_password,
    upsert_app_user,
)


bp_users = Blueprint("users", __name__)


def _users_page_context():
    app_users_list = list_app_users()
    pending_users_list = [u for u in app_users_list if not u.get("is_active")]
    with get_db_connection() as conn:
        admin_audit_logs = conn.execute(
            """
            SELECT action_type, actor_username, target_username, ip_address, details, created_at
            FROM admin_audit_logs
            ORDER BY created_at DESC
            LIMIT 30
            """
        ).fetchall()

    return {
        "app_users_list": app_users_list,
        "pending_users_list": pending_users_list,
        "admin_audit_logs": [dict(row) for row in admin_audit_logs],
    }


@bp_users.route("/admin/users")
@superuser_required
def users_admin():
    return render_template("admin_users.html", **_users_page_context())


@bp_users.route("/admin/users/debug")
@superuser_required
def debug_users():
    from flask import jsonify

    with get_db_connection() as conn:
        app_users = conn.execute("SELECT username, display_name FROM app_users").fetchall()
        ad_users = conn.execute("SELECT username, real_name, fuero FROM ad_users").fetchall()
    return jsonify({
        "app_users": [dict(r) for r in app_users],
        "ad_users": [dict(r) for r in ad_users]
    })


@bp_users.route("/admin/users/ad_profile", methods=["POST"])
@superuser_required
def update_user_phone():
    username = request.form.get("username", "").strip().lower()
    old_username = request.form.get("old_username", "").strip().lower()
    realname = request.form.get("realname", "").strip()
    phone = request.form.get("phone", "").strip()
    fuero = request.form.get("fuero", "").strip()

    if username:
        try:
            with get_db_connection() as conn:
                if old_username and old_username != username:
                    conn.execute("DELETE FROM ad_users WHERE username = %s", (old_username,))

                conn.execute(
                    """
                    INSERT INTO ad_users (username, real_name, phone, fuero)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        phone = VALUES(phone),
                        real_name = VALUES(real_name),
                        fuero = VALUES(fuero)
                    """,
                    (username, realname, phone, fuero),
                )
                log_admin_event(
                    conn,
                    action_type="UPDATE_AD_PROFILE",
                    actor_username=current_username(),
                    target_username=username,
                    ip_address=request.remote_addr,
                    details={"real_name": realname, "phone": phone, "fuero": fuero},
                )
                conn.commit()
                flash(f"Perfil complementario de '{username}' actualizado.", "success")
        except Exception as exc:
            flash(f"Error actualizando datos complementarios: {exc}", "error")
    return redirect(url_for("users.users_admin"))


@bp_users.route("/admin/users/create", methods=["POST"])
@superuser_required
def create_app_user():
    payload = normalize_managed_user_form(request.form)

    try:
        validate_managed_user_payload(payload)
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(url_for("users.users_admin"))

    hydrate_existing_user_defaults(payload)
    existing_user = payload["existing_user"]

    if not payload["is_edit_mode"] and existing_user:
        flash(f"Error: El usuario '{payload['username']}' ya existe. Si desea modificarlo, use la edición directa.", "error")
        return redirect(url_for("users.users_admin"))

    if not payload["is_edit_mode"] and not payload["password"]:
        flash("Error: La contraseña es obligatoria para nuevos usuarios.", "error")
        return redirect(url_for("users.users_admin"))

    try:
        upsert_app_user(
            username=payload["username"],
            password=payload["password"],
            display_name=payload["display_name"],
            is_superuser_flag=payload["is_superuser_flag"],
            is_active=payload["is_active"] or payload["is_superuser_flag"],
            must_change_password=payload["must_change_password"],
            role=payload["role"],
            technician_name=payload["technician_name"],
            permissions=payload["permissions"],
            phone=payload["phone"],
        )
        with get_db_connection() as conn:
            log_admin_event(
                conn,
                action_type="UPDATE_USER" if payload["is_edit_mode"] else "CREATE_USER",
                actor_username=current_username(),
                target_username=payload["username"],
                ip_address=request.remote_addr,
                details={
                    "role": payload["role"],
                    "is_active": bool(payload["is_active"] or payload["is_superuser_flag"]),
                    "is_superuser": bool(payload["is_superuser_flag"]),
                    "must_change_password": bool(payload["must_change_password"]),
                    "permissions": payload["permissions"],
                },
            )
            conn.commit()
        msg = f"Usuario '{payload['username']}' actualizado." if payload["is_edit_mode"] else f"Usuario '{payload['username']}' creado correctamente."
        flash(msg, "success")
    except Exception as exc:
        flash(f"Error al procesar usuario: {exc}", "error")

    return redirect(url_for("users.users_admin"))


@bp_users.route("/admin/users/<username>/approve", methods=["POST"])
@superuser_required
def approve_app_user(username):
    username = (username or "").strip().lower()
    role = request.form.get("role", "tecnico").strip().lower()
    existing_user = _fetch_auth_user(username)

    if not existing_user:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("users.users_admin"))

    try:
        upsert_app_user(
            username=username,
            password="",
            display_name=existing_user.get("display_name") or username,
            is_superuser_flag=bool(existing_user.get("is_superuser")),
            is_active=True,
            must_change_password=bool(existing_user.get("must_change_password")),
            role=role,
            technician_name=existing_user.get("technician_name") or "",
            permissions=None,
            phone=existing_user.get("phone") or "",
        )
        with get_db_connection() as conn:
            log_admin_event(
                conn,
                action_type="APPROVE_USER",
                actor_username=current_username(),
                target_username=username,
                ip_address=request.remote_addr,
                details={"role": role},
            )
            conn.commit()
        flash(f"Usuario '{username}' aprobado y activado.", "success")
    except Exception as exc:
        flash(f"No se pudo aprobar el usuario: {exc}", "error")

    return redirect(url_for("users.users_admin"))


@bp_users.route("/admin/users/reset_password", methods=["POST"])
@superuser_required
def reset_app_user_password():
    username = request.form.get("username", "").strip().lower()
    new_password = request.form.get("password", "")
    if not username or not new_password:
        flash("Usuario y nueva clave son obligatorios.", "error")
    else:
        try:
            update_app_user_password(username, new_password)
            with get_db_connection() as conn:
                log_admin_event(
                    conn,
                    action_type="RESET_PASSWORD",
                    actor_username=current_username(),
                    target_username=username,
                    ip_address=request.remote_addr,
                    details={"forced_reset": True},
                )
                conn.commit()
            flash(f"Clave de '{username}' actualizada correctamente.", "success")
        except Exception as exc:
            flash(f"Error al restablecer clave: {exc}", "error")
    return redirect(url_for("users.users_admin"))


@bp_users.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@superuser_required
def remove_app_user(user_id):
    try:
        user = next((row for row in list_app_users() if row["id"] == user_id), None)
        delete_app_user(user_id, acting_username=current_username())
        with get_db_connection() as conn:
            log_admin_event(
                conn,
                action_type="DELETE_USER",
                actor_username=current_username(),
                target_username=(user or {}).get("username", ""),
                ip_address=request.remote_addr,
                details={"user_id": user_id},
            )
            conn.commit()
        flash("Usuario del sistema eliminado.", "success")
    except Exception as exc:
        flash(f"No se pudo eliminar el usuario: {exc}", "error")
    return redirect(url_for("users.users_admin"))
