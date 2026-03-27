from database.db_core import get_db_connection

with get_db_connection() as conn:
    print('--- COLLATION CHECK ---')
    pcs_col = conn.execute('SHOW FULL COLUMNS FROM pcs WHERE Field = "pc_name"').fetchone()
    link_col = conn.execute('SHOW FULL COLUMNS FROM pc_network_printers WHERE Field = "pc_name"').fetchone()
    print(f"PCS Collation: {pcs_col['Collation']}")
    print(f"Links Collation: {link_col['Collation']}")
    
    print('\n--- DATA CASE CHECK ---')
    sample_pcs = conn.execute('SELECT pc_name FROM pcs WHERE pc_name LIKE "PC-GUSTAVO%"').fetchall()
    sample_links = conn.execute('SELECT pc_name FROM pc_network_printers WHERE pc_name LIKE "PC-GUSTAVO%"').fetchall()
    for row in sample_pcs: print(f"PC table: '{row['pc_name']}'")
    for row in sample_links: print(f"Link table: '{row['pc_name']}'")
