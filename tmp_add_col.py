from database.db_core import get_db_connection
with get_db_connection() as conn:
    try:
        conn.execute("ALTER TABLE pcs ADD COLUMN printer_sn text AFTER printer_port")
        print("Column printer_sn added to pcs table")
    except Exception as e:
        print(f"Error adding column: {e}")
    conn.commit()
