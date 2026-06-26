import os
import logging
from database.db_core import get_db_connection

def notify_all_technicians(title, body, url="/tecnicos", sender="Sistema", task_id=None, msg_type="direct"):
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

    # 2. Log to internal private messages queue (for popups) - Fanned out to all
    try:
        from utils.auth import list_technician_users
        techs = list_technician_users()
        
        with get_db_connection() as conn:
            for tech in techs:
                conn.execute(
                    "INSERT INTO tech_messages (technician_name, sender, task_id, msg_type, title, body, url) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (tech['name'], sender, task_id, msg_type, title, body, url)
                )
            conn.commit()
            logging.info(f"[INTERNAL MSG] Broadcast message queued for {len(techs)} technicians.")
        return {"success": True, "error": None}
    except Exception as e:
        logging.error(f"[ERROR] Internal message queue failed: {e}")
        return {"success": False, "error": str(e)}

def notify_technician(technician_name, title, body, url="/tecnicos", sender="Sistema", task_id=None, msg_type="direct"):
    """
    Sends an internal private message to a specific technician.
    Only logs to `tech_messages` (for the native popup) to maintain privacy.
    """
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO tech_messages (technician_name, sender, task_id, msg_type, title, body, url) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (technician_name, sender, task_id, msg_type, title, body, url)
            )
            conn.commit()
            logging.info(f"[INTERNAL MSG] Private message queued for {technician_name}.")
        return {"success": True, "error": None}
    except Exception as e:
        logging.error(f"[ERROR] Internal private message failed for {technician_name}: {e}")
        return {"success": False, "error": str(e)}
