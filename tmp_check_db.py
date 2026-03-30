
from database.db_core import get_db_connection
try:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT pc_name, is_active FROM pcs").fetchall()
        for r in rows:
            print(f"Name: {r['pc_name']}, Active: {r['is_active']}")
except Exception as e:
    print(f"Error connecting to database: {e}")
