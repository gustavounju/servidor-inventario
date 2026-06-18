from database.db_core import get_db_connection

with get_db_connection() as conn:
    rows = conn.execute("SELECT pc_name, is_active FROM pcs").fetchall()
    for row in rows:
        name = row['pc_name']
        if 'GENERICA' in name.upper() or 'INFRAESTRUCTURA' in name.upper():
            print(f"Name: '{name}' | Length: {len(name)} | Hex: {name.encode().hex()}")
