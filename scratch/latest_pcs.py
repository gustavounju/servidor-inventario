from database.db_core import get_db_connection
with get_db_connection() as conn:
    rows = conn.execute('SELECT pc_name, last_report FROM pcs ORDER BY last_report DESC LIMIT 10').fetchall()
    for r in rows:
        print(f"{r['pc_name']} - {r['last_report']}")
