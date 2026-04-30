from database.db_core import get_db_connection
from utils.constants import detect_fuero

def get_fuero_summary_data():
    """Obtiene estadísticas generales por fuero."""
    with get_db_connection() as conn:
        fueros_rows = conn.execute("SELECT DISTINCT fuero FROM pcs WHERE fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido' ORDER BY fuero").fetchall()
        fueros_list = [row['fuero'] for row in fueros_rows]

        # PCs por Fuero
        pc_counts = conn.execute("""
            SELECT fuero, COUNT(*) as cnt
            FROM pcs
            WHERE is_active = 'True'
              AND fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido'
              AND UPPER(pc_name) NOT IN ('PC GENERICA','INFRAESTRUCTURA','PC-GENERICA')
            GROUP BY fuero
        """).fetchall()

        # Usuarios por Fuero
        user_counts = conn.execute("""
            SELECT f.fuero, COUNT(DISTINCT u.username) as cnt
            FROM (SELECT DISTINCT fuero FROM pcs WHERE fuero IS NOT NULL AND fuero != '') f
            JOIN (
                SELECT username, fuero FROM ad_users
                UNION
                SELECT LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) as username, fuero 
                FROM pcs 
                WHERE is_active = 'True' AND last_user IS NOT NULL AND last_user != ''
            ) u ON u.fuero = f.fuero
            GROUP BY f.fuero
        """).fetchall()

        # Impresoras
        net_printer_counts = conn.execute("""
            SELECT fuero, COUNT(*) as cnt FROM network_printers
            WHERE fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido'
            GROUP BY fuero
        """).fetchall()

        local_printer_counts = conn.execute("""
            SELECT fuero, COUNT(*) as cnt FROM pcs
            WHERE is_active = 'True'
              AND (printer_model IS NOT NULL AND printer_model != '' AND printer_model != 'N/A' AND UPPER(printer_model) NOT LIKE '%%SIN IMPRESORA%%')
              AND (printer_port IS NULL OR printer_port NOT LIKE '\\\\\\\\%%')
              AND fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido'
              AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers)
            GROUP BY fuero
        """).fetchall()

        stats = {}
        for row in pc_counts:
            stats.setdefault(row['fuero'], {'pcs': 0, 'printers': 0, 'users': 0})['pcs'] = row['cnt']
        for row in user_counts:
            stats.setdefault(row['fuero'], {'pcs': 0, 'printers': 0, 'users': 0})['users'] = row['cnt']
        for row in net_printer_counts:
            stats.setdefault(row['fuero'], {'pcs': 0, 'printers': 0, 'users': 0})['printers'] += row['cnt']
        for row in local_printer_counts:
            stats.setdefault(row['fuero'], {'pcs': 0, 'printers': 0, 'users': 0})['printers'] += row['cnt']

        return fueros_list, stats

def get_fuero_detail_data(fuero_name):
    """Obtiene el detalle de elementos (PCs, Usuarios, Impresoras) de un fuero específico."""
    with get_db_connection() as conn:
        if fuero_name:
            pcs = conn.execute("""
                SELECT p.pc_name, p.last_user, p.ip_address, p.os_name, p.printer_model, p.printer_port, p.printer_sn,
                (SELECT COUNT(*) FROM components c WHERE (c.serial_number = p.printer_sn AND p.printer_sn != 'N/A') OR (c.component_type LIKE 'Imp%%' AND c.assigned_pc = p.pc_name)) as is_stocked
                FROM pcs p
                WHERE p.is_active = 'True' AND UPPER(p.pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA') AND p.fuero = %s 
                ORDER BY p.pc_name
            """, (fuero_name,)).fetchall()
            
            users = conn.execute("""
                SELECT username, real_name, phone FROM ad_users WHERE fuero = %s 
                UNION
                SELECT DISTINCT LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) as username, COALESCE(u.real_name, p.last_user) as real_name, u.phone
                FROM pcs p
                LEFT JOIN ad_users u ON LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username
                WHERE p.is_active = 'True' AND p.fuero = %s AND p.last_user IS NOT NULL AND p.last_user != ''
                ORDER BY real_name
            """, (fuero_name, fuero_name)).fetchall()
            
            printers_raw = conn.execute("""
                SELECT DISTINCT np.id, np.ip_address, np.serial_number, np.brand_model, np.fuero as physical_fuero 
                FROM network_printers np
                LEFT JOIN pc_network_printers pnp ON np.id = pnp.printer_id
                LEFT JOIN pcs p ON pnp.pc_name = p.pc_name
                WHERE np.fuero = %s OR p.fuero = %s 
                ORDER BY np.ip_address
            """, (fuero_name, fuero_name)).fetchall()
        else:
            # Huérfanos
            pcs = conn.execute("""
                SELECT p.pc_name, p.last_user, p.ip_address, p.os_name, p.printer_model, p.printer_port, p.printer_sn,
                (SELECT COUNT(*) FROM components c WHERE (c.serial_number = p.printer_sn AND p.printer_sn != 'N/A') OR (c.component_type LIKE 'Imp%%' AND c.assigned_pc = p.pc_name)) as is_stocked
                FROM pcs p
                WHERE p.is_active = 'True' AND UPPER(p.pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA') AND (p.fuero IS NULL OR p.fuero = '' OR p.fuero = 'Desconocido') 
                ORDER BY p.pc_name
            """).fetchall()
            
            users = conn.execute("""
                SELECT username, real_name, phone FROM ad_users WHERE (fuero IS NULL OR fuero = '' OR fuero = 'Desconocido') 
                UNION
                SELECT DISTINCT LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) as username, COALESCE(u.real_name, p.last_user) as real_name, u.phone
                FROM pcs p
                LEFT JOIN ad_users u ON LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username
                WHERE p.is_active = 'True' AND (p.fuero IS NULL OR p.fuero = '' OR p.fuero = 'Desconocido') AND p.last_user IS NOT NULL AND p.last_user != ''
                ORDER BY real_name
            """).fetchall()
            
            printers_raw = conn.execute("""
                SELECT DISTINCT np.id, np.ip_address, np.serial_number, np.brand_model, np.fuero as physical_fuero 
                FROM network_printers np
                LEFT JOIN pc_network_printers pnp ON np.id = pnp.printer_id
                LEFT JOIN pcs p ON pnp.pc_name = p.pc_name
                WHERE (np.fuero IS NULL OR np.fuero = '' OR np.fuero = 'Desconocido') OR (p.fuero IS NULL OR p.fuero = '' OR p.fuero = 'Desconocido')
                ORDER BY np.ip_address
            """).fetchall()

        printers = []
        for p_row in printers_raw:
            p_dict = dict(p_row)
            p_dict['assignments'] = conn.execute("""
                SELECT p.pc_name, p.last_user, u.real_name 
                FROM pc_network_printers pnp
                JOIN pcs p ON pnp.pc_name = p.pc_name
                LEFT JOIN ad_users u ON LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username
                WHERE pnp.printer_id = %s
            """, (p_dict['id'],)).fetchall()
            printers.append(p_dict)

        return pcs, users, printers


def recalculate_all_pc_fueros(conn):
    """Recalcula el fuero detectado para todas las PCs segun el nombre del equipo."""
    pcs = conn.execute("SELECT pc_name, fuero FROM pcs").fetchall()
    updated = 0
    changed = 0
    for pc in pcs:
        name = pc["pc_name"]
        previous_fuero = pc.get("fuero")
        new_fuero = detect_fuero(name)
        conn.execute(
            "UPDATE pcs SET fuero = %s WHERE pc_name = %s",
            (new_fuero, name),
        )
        updated += 1
        if (previous_fuero or "") != new_fuero:
            changed += 1
    return {"updated": updated, "changed": changed}
