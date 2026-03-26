from database.db_core import get_db_connection
with get_db_connection() as conn:
    row = conn.execute("SELECT pc_name, printer_port, printer_model, alerta_impresora_red FROM pcs WHERE pc_name = 'TFSIIIV9000018'").fetchone()
    if row:
        print(f"PC: {row['pc_name']}")
        print(f"Port: {row['printer_port']}")
        print(f"Model: {row['printer_model']}")
        print(f"Alerta Red: {row['alerta_impresora_red']}")
    else:
        print("PC not found")
