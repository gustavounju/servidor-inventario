from database.db_core import get_db_connection
import json

with get_db_connection() as conn:
    print('--- NETWORK PRINTERS ---')
    net_printers = [dict(row) for row in conn.execute('SELECT * FROM network_printers').fetchall()]
    print(f'Count: {len(net_printers)}')
    for p in net_printers:
        print(f"IP: {p['ip_address']} | Model: {p['brand_model']} | SN: {p['serial_number']}")
        
    print('\n--- LOCAL PRINTERS (on PCs) ---')
    query = """
        SELECT pc_name, printer_model, printer_port 
        FROM pcs 
        WHERE is_active = 'True' 
        AND (printer_model IS NOT NULL AND printer_model != '' AND printer_model != 'N/A' AND UPPER(printer_model) NOT LIKE '%%SIN IMPRESORA%%')
        AND (printer_port IS NULL OR printer_port NOT LIKE '\\\\\\\\%%') 
        AND alerta_impresora_red = 0
    """
    loc_printers = [dict(row) for row in conn.execute(query).fetchall()]
    print(f'Count: {len(loc_printers)}')
    for lp in loc_printers:
        print(f"PC: {lp['pc_name']} | Model: {lp['printer_model']} | Port: {lp['printer_port']}")

    print(f'\nTOTAL KPI: {len(net_printers) + len(loc_printers)}')
