from database.db_core import get_db_connection
with get_db_connection() as conn:
    rows = conn.execute("SELECT pc_name FROM pcs LIMIT 20").fetchall()
    for row in rows:
        print(f"[{row['pc_name']}]")
