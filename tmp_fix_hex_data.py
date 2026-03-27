from database.db_core import get_db_connection
from utils.constants import clean_hex_string

def fix_existing_data():
    with get_db_connection() as conn:
        # 1. Network Printers
        printers = conn.execute("SELECT id, serial_number FROM network_printers").fetchall()
        for p in printers:
            clean = clean_hex_string(p['serial_number'])
            if clean != p['serial_number']:
                print(f"Fixing Network Printer {p['id']}: {p['serial_number']} -> {clean}")
                conn.execute("UPDATE network_printers SET serial_number = %s WHERE id = %s", (clean, p['id']))
        
        # 2. PCs (Local Printers)
        pcs = conn.execute("SELECT pc_name, printer_sn FROM pcs WHERE printer_sn IS NOT NULL").fetchall()
        for pc in pcs:
            clean = clean_hex_string(pc['printer_sn'])
            if clean != pc['printer_sn']:
                print(f"Fixing PC {pc['pc_name']}: {pc['printer_sn']} -> {clean}")
                conn.execute("UPDATE pcs SET printer_sn = %s WHERE pc_name = %s", (clean, pc['pc_name']))
        
        conn.commit()
    print("Cleanup finished!")

if __name__ == "__main__":
    fix_existing_data()
