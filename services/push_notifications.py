import hashlib
import json
import logging
import os
from datetime import datetime
from urllib.parse import urlparse
from database.db_core import get_db_connection

logger = logging.getLogger(__name__)


def web_push_enabled():
    return bool(os.environ.get("VAPID_PUBLIC_KEY") and os.environ.get("VAPID_PRIVATE_KEY"))


TASK_PUSH_ACCENTS = {
    "pc": {"marker": "🟦", "accent": "blue", "label": "PC"},
    "loose": {"marker": "🟪", "accent": "violet", "label": "General"},
    "operator": {"marker": "🟧", "accent": "amber", "label": "Operador"},
    "assigned": {"marker": "🟩", "accent": "mint", "label": "Asignada"},
}


def _clip(value, limit):
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _line(label, value, icon):
    value = _clip(value, 220)
    if not value:
        return None
    return {"label": label, "value": value, "icon": icon}


def build_new_task_push(
    *,
    task_id=None,
    source="pc",
    pc_name="",
    solicitante="",
    descripcion="",
    categoria="",
    fuero="",
    assigned_to="",
    phone="",
    operator_name="",
):
    """Arma un payload consistente para notificaciones nativas de nuevas tareas."""
    visual = TASK_PUSH_ACCENTS.get(source, TASK_PUSH_ACCENTS["pc"])
    title = f"{visual['marker']} Nueva tarea · {visual['label']}"
    now_label = datetime.now().strftime("%d/%m %H:%M")
    lines = [
        _line("Hora", now_label, "🕒"),
        _line("Equipo", pc_name, "💻"),
        _line("Área", fuero, "🏛️"),
        _line("Solicitante", solicitante, "👤"),
        _line("Teléfono", phone, "📞"),
        _line("Categoría", categoria, "🏷️"),
        _line("Asignada a", assigned_to, "🧑‍🔧"),
        _line("Operador", operator_name, "🎧"),
        _line("Detalle", descripcion, "📝"),
    ]
    lines = [line for line in lines if line]
    body = "\n".join(f"{line['icon']} {line['label']}: {line['value']}" for line in lines)
    return {
        "title": title,
        "body": body,
        "url": f"/tecnicos?task_id={task_id}" if task_id else "/tecnicos",
        "task_id": task_id,
        "payload_extra": {
            "kind": "new_task",
            "accent": visual["accent"],
            "lines": lines,
            "category": _clip(categoria, 80),
            "pc_name": _clip(pc_name, 80),
        },
    }


def _subscription_is_valid(subscription):
    if not isinstance(subscription, dict):
        return False
    endpoint = subscription.get("endpoint")
    keys = subscription.get("keys") or {}
    parsed = urlparse(str(endpoint or ""))
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and len(str(endpoint)) <= 4096
        and len(str(keys.get("p256dh") or "")) <= 512
        and len(str(keys.get("auth") or "")) <= 512
    )


def save_web_push_subscription(technician_name, subscription, user_agent=""):
    """Guarda/actualiza una suscripción validada para el técnico autenticado."""
    if not technician_name or not _subscription_is_valid(subscription):
        return False
    endpoint = str(subscription["endpoint"])
    keys = subscription.get("keys") or {}
    p256dh = str(keys.get("p256dh") or "")
    auth = str(keys.get("auth") or "")
    if not p256dh or not auth:
        return False
    endpoint_hash = hashlib.sha256(endpoint.encode("utf-8")).hexdigest()
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO web_push_subscriptions
                (technician_name, endpoint, endpoint_hash, p256dh, auth, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                technician_name = VALUES(technician_name),
                endpoint = VALUES(endpoint),
                p256dh = VALUES(p256dh),
                auth = VALUES(auth),
                user_agent = VALUES(user_agent),
                updated_at = CURRENT_TIMESTAMP
            """,
            (technician_name[:255], endpoint, endpoint_hash, p256dh, auth, str(user_agent or "")[:255]),
        )
    return True


def remove_web_push_subscription(technician_name, endpoint):
    if not technician_name or not endpoint or len(str(endpoint)) > 4096:
        return False
    endpoint_hash = hashlib.sha256(str(endpoint).encode("utf-8")).hexdigest()
    with get_db_connection() as conn:
        conn.execute(
            "DELETE FROM web_push_subscriptions WHERE technician_name=%s AND endpoint_hash=%s",
            (technician_name, endpoint_hash),
        )
    return True


def _send_web_push(title, body, url, task_id=None, technician_name=None, payload_extra=None):
    """Envía push a dispositivos suscritos; nunca interrumpe la creación de tareas."""
    if not web_push_enabled():
        return {"sent": 0, "enabled": False}
    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.error("Web Push configurado pero pywebpush no está instalado")
        return {"sent": 0, "enabled": False}

    query = "SELECT id, technician_name, endpoint, p256dh, auth FROM web_push_subscriptions"
    params = ()
    if technician_name:
        query += " WHERE technician_name=%s"
        params = (technician_name,)
    try:
        with get_db_connection() as conn:
            subscriptions = conn.execute(query, params).fetchall()
    except Exception:
        logger.exception("No se pudieron cargar las suscripciones Web Push")
        return {"sent": 0, "enabled": True}

    payload_data = {
        "title": str(title or "Nueva notificación")[:160],
        "body": str(body or "")[:1000],
        "url": str(url or "/tecnicos")[:512],
        "task_id": task_id,
    }
    if isinstance(payload_extra, dict):
        payload_data.update(payload_extra)
    payload = json.dumps(payload_data, ensure_ascii=False)
    sent = 0
    stale_ids = []
    claims = {"sub": os.environ.get("VAPID_CLAIMS_EMAIL", "mailto:admin@example.invalid")}
    for row in subscriptions:
        info = {
            "endpoint": row["endpoint"],
            "keys": {"p256dh": row["p256dh"], "auth": row["auth"]},
        }
        try:
            webpush(
                subscription_info=info,
                data=payload,
                vapid_private_key=os.environ["VAPID_PRIVATE_KEY"],
                vapid_claims=claims,
                ttl=300,
            )
            sent += 1
        except WebPushException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):
                stale_ids.append(row["id"])
            logger.warning("Web Push no entregado para una suscripción (HTTP %s)", status or "error")
        except Exception:
            logger.exception("Error enviando Web Push")
    if stale_ids:
        placeholders = ",".join(["%s"] * len(stale_ids))
        with get_db_connection() as conn:
            conn.execute(f"DELETE FROM web_push_subscriptions WHERE id IN ({placeholders})", tuple(stale_ids))
    return {"sent": sent, "enabled": True}

def notify_all_technicians(title, body, url="/tecnicos", sender="Sistema", task_id=None, msg_type="system", scheduled_for=None, payload_extra=None):
    """
    Sends an internal notification to all technicians.
    Logs to both `app_notifications` (for the global bell) and `tech_messages` (for the native popup).
    """
    # 1. Log to global notifications (Avisos tab)
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO app_notifications (title, body, url) VALUES (%s, %s, %s)",
                (title, body, url)
            )
            conn.commit()
            safe_title = title.encode('ascii', 'ignore').decode()
            logging.info(f"[NOTIF] Saved to DB: {safe_title}")
    except Exception as e:
        logging.error(f"[ERROR] DB notification logging failed: {e}")

    _send_web_push(title, body, url, task_id=task_id, payload_extra=payload_extra)

    # 2. Log to internal private messages queue (for popups) - Fanned out to all
    if msg_type != "system":
        try:
            from utils.auth import list_technician_users
            techs = list_technician_users()
            
            with get_db_connection() as conn:
                for tech in techs:
                    conn.execute(
                        "INSERT INTO tech_messages (technician_name, sender, task_id, msg_type, title, body, url, scheduled_for) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (tech['name'], sender, task_id, msg_type, title, body, url, scheduled_for)
                    )
                conn.commit()
                logging.info(f"[INTERNAL MSG] Broadcast message queued for {len(techs)} technicians.")
            return {"success": True, "error": None}
        except Exception as e:
            logging.error(f"[ERROR] Internal message queue failed: {e}")
            return {"success": False, "error": str(e)}
    return {"success": True, "error": None}

def notify_technician(technician_name, title, body, url="/tecnicos", sender="Sistema", task_id=None, msg_type="direct", scheduled_for=None, payload_extra=None):
    """
    Sends an internal private message to a specific technician.
    Only logs to `tech_messages` (for the native popup) to maintain privacy.
    """
    try:
        _send_web_push(title, body, url, task_id=task_id, technician_name=technician_name, payload_extra=payload_extra)
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO tech_messages (technician_name, sender, task_id, msg_type, title, body, url, scheduled_for) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (technician_name, sender, task_id, msg_type, title, body, url, scheduled_for)
            )
            conn.commit()
            logging.info(f"[INTERNAL MSG] Private message queued for {technician_name}.")
        return {"success": True, "error": None}
    except Exception as e:
        logging.error(f"[ERROR] Internal private message failed for {technician_name}: {e}")
        return {"success": False, "error": str(e)}
