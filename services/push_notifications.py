def notify_all_technicians(title, body, url="/mobile"):
    """
    Logs a notification to the internal database for the 'Avisos' tab.
    All external connections (ntfy, WhatsApp, Web Push) have been removed.
    """
    # --- INTERNAL: Log to Database History ---
    try:
        from database.db_core import get_db_connection
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO app_notifications (title, body, url) VALUES (%s, %s, %s)",
                (title, body, url)
            )
            conn.commit()
            # Avoid printing emojis directly to prevent encoding errors on some Windows consoles
            safe_title = title.encode('ascii', 'ignore').decode()
            print(f"[LOG] Notification saved to DB: {safe_title}")
    except Exception as e:
        print(f"[ERROR] Error logging notification to DB: {e}")

