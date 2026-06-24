from flask import Blueprint, flash, redirect, render_template, request, url_for

from database.db_core import get_db_connection
from services.admin_audit import log_admin_event
from services.fuero_service import recalculate_all_pc_fueros
from services.user_admin import (
    hydrate_existing_user_defaults,
    normalize_managed_user_form,
    validate_managed_user_payload,
)
from utils.constants import invalidate_fuero_mapping_cache
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
        ad_usernames = {
            str(row["username"]).strip().lower()
            for row in conn.execute("SELECT username FROM ad_users").fetchall()
            if row.get("username")
        }
        fuero_mappings = conn.execute(
            """
            SELECT id, prefix_code, fuero_label, notes, is_active, updated_at
            FROM fuero_mappings
            ORDER BY is_active DESC, fuero_label ASC, prefix_code ASC
            """
        ).fetchall()
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
        "ad_usernames": ad_usernames,
        "fuero_mappings": [dict(row) for row in fuero_mappings],
        "admin_audit_logs": [dict(row) for row in admin_audit_logs],
    }


def _is_ad_username(username):
    username = (username or "").strip().lower()
    if not username:
        return False
    with get_db_connection() as conn:
        row = conn.execute("SELECT 1 FROM ad_users WHERE LOWER(username) = %s LIMIT 1", (username,)).fetchone()
    return bool(row)


def _fuero_admin_context():
    with get_db_connection() as conn:
        fuero_mappings = conn.execute(
            """
            SELECT id, prefix_code, fuero_label, notes, is_active, updated_at
            FROM fuero_mappings
            ORDER BY is_active DESC, fuero_label ASC, prefix_code ASC
            """
        ).fetchall()
    return {
        "fuero_mappings": [dict(row) for row in fuero_mappings],
    }


def _safe_next_url(default_endpoint="users.users_admin"):
    next_url = (request.form.get("next_url") or request.args.get("next_url") or "").strip()
    if next_url.startswith("/"):
        return next_url
    return url_for(default_endpoint)


@bp_users.route("/admin/users")
@superuser_required
def users_admin():
    return render_template("admin_users.html", **_users_page_context())


@bp_users.route("/admin/fueros")
@superuser_required
def fueros_admin():
    return render_template("fuero_admin_modal.html", **_fuero_admin_context())


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
        return redirect(_safe_next_url())

    hydrate_existing_user_defaults(payload)
    existing_user = payload["existing_user"]
    is_ad_user = _is_ad_username(payload["username"])

    if not payload["is_edit_mode"] and existing_user:
        flash(f"Error: El usuario '{payload['username']}' ya existe. Si desea modificarlo, use la edición directa.", "error")
        return redirect(_safe_next_url())

    if is_ad_user and payload["password"]:
        payload["password"] = ""

    if not payload["is_edit_mode"] and not payload["password"] and not is_ad_user:
        flash("Error: La contraseña es obligatoria para nuevos usuarios locales.", "error")
        return redirect(_safe_next_url())

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

    return redirect(_safe_next_url())


def _normalize_fuero_mapping_payload(form):
    mapping_id = (form.get("mapping_id") or "").strip()
    prefix_code = (form.get("prefix_code") or "").strip().upper()
    fuero_label = (form.get("fuero_label") or "").strip()
    notes = (form.get("notes") or "").strip()
    is_active = form.get("is_active") == "on"
    apply_recalc = form.get("apply_recalc") == "on"

    if not prefix_code:
        raise ValueError("El prefijo del fuero es obligatorio.")
    if not fuero_label:
        raise ValueError("La descripcion del fuero es obligatoria.")

    return {
        "mapping_id": int(mapping_id) if mapping_id.isdigit() else None,
        "prefix_code": prefix_code,
        "fuero_label": fuero_label,
        "notes": notes,
        "is_active": is_active,
        "apply_recalc": apply_recalc,
    }


@bp_users.route("/admin/fueros/save", methods=["POST"])
@superuser_required
def save_fuero_mapping():
    redirect_target = _safe_next_url()
    try:
        payload = _normalize_fuero_mapping_payload(request.form)
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(redirect_target)

    try:
        with get_db_connection() as conn:
            previous = None
            if payload["mapping_id"]:
                previous = conn.execute(
                    """
                    SELECT id, prefix_code, fuero_label, notes, is_active
                    FROM fuero_mappings
                    WHERE id = %s
                    """,
                    (payload["mapping_id"],),
                ).fetchone()

            if payload["mapping_id"]:
                conn.execute(
                    """
                    UPDATE fuero_mappings
                    SET prefix_code = %s, fuero_label = %s, notes = %s, is_active = %s
                    WHERE id = %s
                    """,
                    (
                        payload["prefix_code"],
                        payload["fuero_label"],
                        payload["notes"] or None,
                        1 if payload["is_active"] else 0,
                        payload["mapping_id"],
                    ),
                )
                action_type = "UPDATE_FUERO_MAPPING"
            else:
                conn.execute(
                    """
                    INSERT INTO fuero_mappings (prefix_code, fuero_label, notes, is_active)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        payload["prefix_code"],
                        payload["fuero_label"],
                        payload["notes"] or None,
                        1 if payload["is_active"] else 0,
                    ),
                )
                payload["mapping_id"] = conn.cursor.lastrowid
                action_type = "CREATE_FUERO_MAPPING"

            invalidate_fuero_mapping_cache()

            recalc_result = None
            if payload["apply_recalc"]:
                recalc_result = recalculate_all_pc_fueros(conn)

            log_admin_event(
                conn,
                action_type=action_type,
                actor_username=current_username(),
                target_username=payload["prefix_code"],
                ip_address=request.remote_addr,
                details={
                    "id": payload["mapping_id"],
                    "before": dict(previous) if previous else None,
                    "after": {
                        "prefix_code": payload["prefix_code"],
                        "fuero_label": payload["fuero_label"],
                        "notes": payload["notes"],
                        "is_active": payload["is_active"],
                    },
                    "recalculate": recalc_result,
                },
            )
            conn.commit()
        invalidate_fuero_mapping_cache()
        flash("Catalogo de fueros actualizado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo guardar el prefijo: {exc}", "error")

    return redirect(redirect_target)


@bp_users.route("/admin/fueros/<int:mapping_id>/delete", methods=["POST"])
@superuser_required
def delete_fuero_mapping(mapping_id):
    redirect_target = _safe_next_url()
    apply_recalc = request.form.get("apply_recalc") == "on"
    try:
        with get_db_connection() as conn:
            previous = conn.execute(
                """
                SELECT id, prefix_code, fuero_label, notes, is_active
                FROM fuero_mappings
                WHERE id = %s
                """,
                (mapping_id,),
            ).fetchone()
            if not previous:
                flash("Prefijo no encontrado.", "error")
                return redirect(redirect_target)

            conn.execute("DELETE FROM fuero_mappings WHERE id = %s", (mapping_id,))
            invalidate_fuero_mapping_cache()

            recalc_result = None
            if apply_recalc:
                recalc_result = recalculate_all_pc_fueros(conn)

            log_admin_event(
                conn,
                action_type="DELETE_FUERO_MAPPING",
                actor_username=current_username(),
                target_username=previous["prefix_code"],
                ip_address=request.remote_addr,
                details={
                    "deleted": dict(previous),
                    "recalculate": recalc_result,
                },
            )
            conn.commit()
        invalidate_fuero_mapping_cache()
        flash("Prefijo eliminado del catalogo.", "success")
    except Exception as exc:
        flash(f"No se pudo eliminar el prefijo: {exc}", "error")
    return redirect(redirect_target)


@bp_users.route("/admin/fueros/recalculate", methods=["POST"])
@superuser_required
def recalculate_fueros():
    redirect_target = _safe_next_url()
    try:
        with get_db_connection() as conn:
            invalidate_fuero_mapping_cache()
            result = recalculate_all_pc_fueros(conn)
            log_admin_event(
                conn,
                action_type="RECALCULATE_FUEROS",
                actor_username=current_username(),
                target_username="pcs",
                ip_address=request.remote_addr,
                details=result,
            )
            conn.commit()
        invalidate_fuero_mapping_cache()
        flash(
            f"Fueros recalculados. PCs revisadas: {result['updated']}. Cambios detectados: {result['changed']}.",
            "success",
        )
    except Exception as exc:
        flash(f"No se pudieron recalcular los fueros: {exc}", "error")
    return redirect(redirect_target)


@bp_users.route("/admin/users/<username>/approve", methods=["POST"])
@superuser_required
def approve_app_user(username):
    username = (username or "").strip().lower()
    role = request.form.get("role", "tecnico").strip().lower()
    existing_user = _fetch_auth_user(username)

    if not existing_user:
        flash("Usuario no encontrado.", "error")
        return redirect(_safe_next_url())

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

    return redirect(_safe_next_url())


@bp_users.route("/admin/users/reset_password", methods=["POST"])
@superuser_required
def reset_app_user_password():
    username = request.form.get("username", "").strip().lower()
    new_password = request.form.get("password", "")
    if not username or not new_password:
        flash("Usuario y nueva clave son obligatorios.", "error")
    elif _is_ad_username(username):
        flash(f"La clave de '{username}' se gestiona por Active Directory y no puede cambiarse desde Inventario.", "error")
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
    return redirect(_safe_next_url())


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
    return redirect(_safe_next_url())


@bp_users.route("/admin/users/sync_ad", methods=["POST"])
@superuser_required
def sync_ad_users_route():
    from services.ad_sync_service import sync_ad_users
    try:
        result = sync_ad_users()
        if result.get("status") == "success":
            flash(result["message"], "success")
        else:
            flash(result.get("message", "Error desconocido al sincronizar AD."), "error")
            
        with get_db_connection() as conn:
            log_admin_event(
                conn,
                action_type="SYNC_AD_USERS",
                actor_username=current_username(),
                target_username="SISTEMA",
                ip_address=request.remote_addr,
                details=result,
            )
            conn.commit()
    except Exception as exc:
        flash(f"Error crítico en sincronización AD: {exc}", "error")
        
    return redirect(_safe_next_url())
