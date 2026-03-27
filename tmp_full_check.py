from database.db_core import get_db_connection
with get_db_connection() as conn:
    rows = conn.execute("SELECT * FROM pcs").fetchall()
    for row in rows:
        print(f"PC: {row['pc_name']} (Active: {row['is_active']})")
        print(f"  Printer: {row['printer_model']} | Port: {row['printer_port']}")

    print("\nPRINTER CATALOG:")
    rows = conn.execute("SELECT * FROM network_printers").fetchall()
    for row in rows:
        print(f"ID: {row['id']} | IP: {row['ip_address']} | Model: {row['brand_model']}")
