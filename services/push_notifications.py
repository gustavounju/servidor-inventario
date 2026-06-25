import os

def notify_all_technicians(title, body, url="/mobile"):
    """
    Sends a Firebase Cloud Messaging (FCM) push notification to all subscribed
    technician devices, AND logs to the internal DB for the Avisos tab.
    """
    # --- 1. INTERNAL: Log to Database ---
    try:
        from database.db_core import get_db_connection
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO app_notifications (title, body, url) VALUES (%s, %s, %s)",
                (title, body, url)
            )
            conn.commit()
            safe_title = title.encode('ascii', 'ignore').decode()
            print(f"[NOTIF] Saved to DB: {safe_title}")
    except Exception as e:
        print(f"[ERROR] DB notification logging failed: {e}")

    # --- 2. EXTERNAL: Firebase Cloud Messaging ---
    try:
        return _send_fcm_push(title, body, url)
    except Exception as e:
        print(f"[ERROR] FCM push failed: {e}")
        return {"success": False, "error": str(e)}


def notify_technician(technician_name, title, body, url="/mobile"):
    """
    Sends a Firebase Cloud Messaging (FCM) push notification to a SPECIFIC
    technician device. Does NOT log to the internal DB to maintain privacy.
    """
    try:
        return _send_fcm_push(title, body, url, technician_name=technician_name)
    except Exception as e:
        print(f"[ERROR] FCM personal push failed for {technician_name}: {e}")
        return {"success": False, "error": str(e)}

def _send_fcm_push(title, body, url="/mobile", technician_name=None):
    """Sends a push notification to FCM tokens via Firebase Admin SDK."""
    cred_path = os.environ.get("FIREBASE_CREDENTIALS", "firebase-credentials.json")

    if not os.path.exists(cred_path):
        err = f"No credentials file found at {cred_path}"
        print(f"[FCM] {err}. Skipping FCM push.")
        return {"success": False, "error": err}

    try:
        import firebase_admin
        from firebase_admin import credentials, messaging

        # Initialize app only once
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        # Get registered tokens from the DB
        from database.db_core import get_db_connection
        with get_db_connection() as conn:
            if technician_name:
                rows = conn.execute("SELECT token FROM fcm_tokens WHERE technician_name = %s", (technician_name,)).fetchall()
            else:
                rows = conn.execute("SELECT token FROM fcm_tokens").fetchall()

        tokens = [r["token"] for r in rows if r.get("token")]
        if not tokens:
            err = f"El técnico '{technician_name}' no tiene dispositivos habilitados para recibir notificaciones." if technician_name else "No hay dispositivos registrados."
            print(f"[FCM] {err}")
            return {"success": False, "error": err}

        # Send to all devices (MulticastMessage)
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={"url": url},
            webpush=messaging.WebpushConfig(
                headers={"Urgency": "high"},
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon="/static/icon-192.png",
                    badge="/static/icon-192.png",
                    silent=False,
                ),
                fcm_options=messaging.WebpushFCMOptions(link=url),
            ),
            tokens=tokens,
        )

        response = messaging.send_each_for_multicast(message)
        print(f"[FCM] Sent: {response.success_count} ok, {response.failure_count} failed")

        # Clean up invalid tokens
        if response.failure_count > 0:
            invalid_tokens = []
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    invalid_tokens.append(tokens[idx])
                    print(f"[FCM] Token failed: {resp.exception}")
            if invalid_tokens:
                from database.db_core import get_db_connection
                with get_db_connection() as conn:
                    for tok in invalid_tokens:
                        conn.execute("DELETE FROM fcm_tokens WHERE token = %s", (tok,))
                    conn.commit()
                print(f"[FCM] Removed {len(invalid_tokens)} invalid token(s).")

        if response.success_count > 0:
            return {"success": True, "error": None}
        else:
            return {"success": False, "error": "Todos los tokens fueron rechazados por Firebase (posiblemente caducados)."}

    except ImportError:
        err = "firebase-admin not installed. Run: pip install firebase-admin"
        print(f"[FCM] {err}")
        return {"success": False, "error": err}
    except Exception as e:
        print(f"[FCM] Error sending push: {e}")
        return {"success": False, "error": str(e)}
