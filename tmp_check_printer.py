from database.db_core import get_db_connection
with get_db_connection() as conn:
    rows = conn.execute("SELECT pc_name, printer_port, printer_model FROM pcs WHERE pc_name LIKE 'TFSIII%'").fetchall()
    for row in rows:
        print(f"PC: {row['pc_name']}")
        print(f"Port: {row['printer_port']}")
        print(f"Model: {row['printer_model']}")
