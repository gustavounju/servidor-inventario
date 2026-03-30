
from database.db_core import get_db_connection
import json
try:
    with get_db_connection() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM app_users").fetchall()]
        print(json.dumps(rows, default=str))
except Exception as e:
    print(f"Error: {e}")
