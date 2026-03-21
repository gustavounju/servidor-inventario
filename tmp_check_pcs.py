from database.db_core import get_db_connection
with get_db_connection() as conn:
    cols = conn.execute("DESCRIBE pcs").fetchall()
    for col in cols:
        print(f"{col['Field']}: {col['Type']}")
