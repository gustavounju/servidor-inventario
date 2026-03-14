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
    Also sends to ntfy.sh as a reliable fallback.
    """
    message = {
        "title": title,
        "body": body,
        "url": url
    }

    # --- EXTERNAL: ntfy.sh (High Reliability) ---
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
        print(f"Notification sent to ntfy topic: {ntfy_topic}")
    except Exception as e:
        print(f"Error sending to ntfy: {e}")

    # --- EXTERNAL: Green-API WhatsApp (Fast) ---
    green_id_instance = os.environ.get("GREEN_API_ID_INSTANCE")
    green_api_token = os.environ.get("GREEN_API_TOKEN_INSTANCE")
    green_phone = os.environ.get("GREEN_API_PHONE")
    
    if green_id_instance and green_api_token and green_phone:
        try:
            # Format message for WhatsApp
            wa_message = f"*{title}*\n{body}\n\n{url}"
            green_url = f"https://api.green-api.com/waInstance{green_id_instance}/sendMessage/{green_api_token}"
            
            # Identify if the target is a group or a private chat
            chat_id = green_phone if "@g.us" in green_phone else f"{green_phone}@c.us"
            
            payload = {
                "chatId": chat_id,
                "message": wa_message
            }
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.post(green_url, json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                print("Notification sent via Green-API WhatsApp")
            else:
                print(f"Green-API Error: {response.text}")
        except Exception as e:
            print(f"Error sending to Green-API: {e}")

    # --- EXTERNAL: Telegram Bot (Fast) ---
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if telegram_token and telegram_chat_id:
        try:
            tg_message = f"*{title}*\n{body}\n\n[Abrir Inventario]({url})"
            tg_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            tg_data = {
                "chat_id": telegram_chat_id,
                "text": tg_message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            response = requests.post(tg_url, json=tg_data, timeout=5)
            if response.status_code == 200:
                print("Notification sent via Telegram Bot")
            else:
                print(f"Telegram Bot Error: {response.text}")
        except Exception as e:
            print(f"Error sending to Telegram: {e}")

    # --- WEB PUSH (Standard) ---
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        print("Push Notifications: VAPID keys not configured. Skipping Web Push.")
        return

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
        
        if expired_endpoints:
            format_strings = ','.join(['%s'] * len(expired_endpoints))
            conn.execute(f"DELETE FROM push_subscriptions WHERE endpoint IN ({format_strings})", tuple(expired_endpoints))
            conn.commit()
