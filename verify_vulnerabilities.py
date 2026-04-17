from database.db_core import get_db_connection

def check_pc(name):
    print(f"\n--- Datos para {name} ---")
    with get_db_connection() as conn:
        pc = conn.execute("SELECT pc_name, printer_sn, printer_port, last_report FROM pcs WHERE pc_name = %s", (name,)).fetchone()
        if pc:
            print(f"PC: {pc['pc_name']}")
            print(f"Serial: {pc['printer_sn']}")
            print(f"Puerto: {pc['printer_port']}")
        else:
            print("No encontrado.")

check_pc("PC-TEST'; DROP TABLE audit_logs; --")
check_pc("WEIRD-SN-PC")
check_pc("EXTREME-HEALTH")
