from database.db_core import get_db_connection
import json

def check_pcs():
    with get_db_connection() as conn:
        pcs = conn.execute("SELECT pc_name, ip_address, printer_model, printer_port, printer_sn FROM pcs").fetchall()
        print(json.dumps([dict(p) for p in pcs], indent=2))

if __name__ == "__main__":
    check_pcs()
