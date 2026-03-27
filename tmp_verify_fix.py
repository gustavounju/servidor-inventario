from database.db_core import get_db_connection

with get_db_connection() as conn:
    net_pr = conn.execute('SELECT COUNT(*) as c FROM network_printers').fetchone()['c']
    loc_pr = conn.execute("""
        SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' 
        AND (printer_model IS NOT NULL AND printer_model != '' AND printer_model != 'N/A' AND UPPER(printer_model) NOT LIKE '%%SIN IMPRESORA%%')
        AND (printer_port IS NULL OR printer_port NOT LIKE '\\\\\\\\%%') AND alerta_impresora_red = 0
        AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers)
    """).fetchone()['c']
    
    print(f'NEW KPI Calculation:')
    print(f'Printers in Catalog (Network): {net_pr}')
    print(f'Printers on PCs (Local, not in Catalog): {loc_pr}')
    print(f'Total KPI: {net_pr + loc_pr}')
