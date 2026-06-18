import sys
import os

# Append the project root to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_core import get_db_connection

with get_db_connection() as conn:
    rows = conn.execute("SELECT id, pc_name, estado FROM tasks ORDER BY id DESC LIMIT 10").fetchall()
    for r in rows:
        print(dict(r))
