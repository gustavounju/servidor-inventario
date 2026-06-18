from database.db_core import get_db_connection

with get_db_connection() as conn:
    print("Updating...")
    conn.execute('UPDATE network_printers SET ip_address = %s, fuero = %s WHERE id = 26', ('\\\\HOST-TEST-01\\HP1102', 'Menores'))
    conn.commit()
    res = conn.execute('SELECT id, ip_address, fuero FROM network_printers WHERE id=26').fetchone()
    print("Result:", dict(res))
