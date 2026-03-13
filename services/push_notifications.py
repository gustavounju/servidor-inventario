import os
import json
from pywebpush import webpush, WebPushException
from database.db_core import get_db_connection

VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")
VAPID_CLAIMS = {
    "sub": "mailto:gustavoeliasm@gmail.com"
}

def send_push_notification(subscription_info, message_data):
    """
    Sends a push notification to a single subscription.
    subscription_info: dict with endpoint, keys (p256dh, auth)
    message_data: dict with title, body, etc.
    """
    try:
        response = webpush(
            subscription_info=subscription_info,
            data=json.dumps(message_data),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        return response.ok
    except WebPushException as ex:
        print(f"WebPush error: {ex}")
        if ex.response and ex.response.status_code == 410:
            # Subscription has expired or is no longer valid
            return "expired"
        return False
    except Exception as e:
        print(f"General Push Error: {e}")
        return False

def notify_all_technicians(title, body, url="/mobile"):
    """
    Fetches all subscriptions and sends a notification to each.
    """
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        print("Push Notifications: VAPID keys not configured.")
        return

    message = {
        "title": title,
        "body": body,
        "url": url
    }

    expired_endpoints = []
    
    with get_db_connection() as conn:
        subscriptions = conn.execute("SELECT * FROM push_subscriptions").fetchall()
        
        for sub in subscriptions:
            sub_info = {
                "endpoint": sub["endpoint"],
                "keys": {
                    "p256dh": sub["p256dh"],
                    "auth": sub["auth"]
                }
            }
            
            result = send_push_notification(sub_info, message)
            if result == "expired":
                expired_endpoints.append(sub["endpoint"])
        
        # Clean up expired subscriptions
        if expired_endpoints:
            format_strings = ','.join(['%s'] * len(expired_endpoints))
            conn.execute(f"DELETE FROM push_subscriptions WHERE endpoint IN ({format_strings})", tuple(expired_endpoints))
            conn.commit()

    # --- FALLBACK / EXTERNAL: ntfy.sh ---
    # Usamos un tópico único basado en el nombre de la app para que todos los técnicos escuchen el mismo
    ntfy_topic = os.environ.get("NTFY_TOPIC", "inventario_gold_alertas_tech")
    try:
        import requests
        requests.post(f"https://ntfy.sh/{ntfy_topic}",
            data=body.encode('utf-8'),
            headers={
                "Title": title.encode('utf-8'),
                "Priority": "high",
                "Tags": "tools,warning",
                "Click": url
            },
            timeout=5
        )
    except Exception as e:
        print(f"Error sending to ntfy: {e}")
