from database.db_core import get_db_connection
with get_db_connection() as conn:
    columns = [dict(r) for r in conn.execute('DESCRIBE tasks').fetchall()]
    for col in columns:
        print(f"{col['Field']}: {col['Type']}")
