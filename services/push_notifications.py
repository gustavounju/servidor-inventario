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
        _send_fcm_push(title, body, url)
    except Exception as e:
        print(f"[ERROR] FCM push failed: {e}")


def _send_fcm_push(title, body, url="/mobile"):
    """Sends a push notification to all stored FCM tokens via Firebase Admin SDK."""
    cred_path = os.environ.get("FIREBASE_CREDENTIALS", "firebase-credentials.json")

    if not os.path.exists(cred_path):
        print("[FCM] No credentials file found. Skipping FCM push.")
        return

    try:
        import firebase_admin
        from firebase_admin import credentials, messaging

        # Initialize app only once
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        # Get all registered tokens from the DB
        from database.db_core import get_db_connection
        with get_db_connection() as conn:
            rows = conn.execute("SELECT token FROM fcm_tokens").fetchall()

        tokens = [r["token"] for r in rows if r.get("token")]
        if not tokens:
            print("[FCM] No registered devices. Skipping.")
            return

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

    except ImportError:
        print("[FCM] firebase-admin not installed. Run: pip install firebase-admin")
    except Exception as e:
        print(f"[FCM] Error sending push: {e}")
