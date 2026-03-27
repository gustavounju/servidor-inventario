from database.db_core import get_db_connection
import json

with get_db_connection() as conn:
    print('--- LINKS FOR LOCAL PRINTER PCS ---')
    links = [dict(row) for row in conn.execute("SELECT pc_name, printer_id FROM pc_network_printers WHERE pc_name IN ('PC-GUSTAVO-LOCAL', 'PC-OTRA-OFICINA')").fetchall()]
    for l in links:
        print(f"PC: {l['pc_name']} | Linked Printer ID: {l['printer_id']}")
    
    print('\n--- PRINTERS IN CATALOG WITH IP LIKE USB ---')
    usb_cat = [dict(row) for row in conn.execute("SELECT id, ip_address, serial_number FROM network_printers WHERE ip_address LIKE 'USB%'").fetchall()]
    for p in usb_cat:
        print(f"ID: {p['id']} | IP: {p['ip_address']} | SN: {p['serial_number']}")
