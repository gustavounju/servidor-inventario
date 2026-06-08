from database.db_core import get_db_connection
from utils.constants import DEFAULT_FUERO_MAPPING
import os

def _get_db_name():
    return os.environ.get("DB_NAME", "inventario_dev")

def _column_exists(conn, table, column):
    """Verifica si una columna existe en una tabla usando INFORMATION_SCHEMA (MySQL)."""
    db_name = _get_db_name()
    result = conn.execute(
        """
        SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (db_name, table, column)
    ).fetchone()
    return result and result["cnt"] > 0

def _table_exists(conn, table):
    """Verifica si una tabla existe usando INFORMATION_SCHEMA (MySQL)."""
    db_name = _get_db_name()
    result = conn.execute(
        """
        SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """,
        (db_name, table)
    ).fetchone()
    return result and result["cnt"] > 0


def _index_exists(conn, table, index_name):
    db_name = _get_db_name()
    result = conn.execute(
        """
        SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND INDEX_NAME = %s
        """,
        (db_name, table, index_name),
    ).fetchone()
    return result and result["cnt"] > 0


def migrate_db_v2():
    """Migración V2: Asegurar columna 'solicitante' en tasks."""
    print("Verificando migración de DB v2...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "tasks", "solicitante"):
            print("Aplicando migración V2: Agregando 'solicitante' a tasks...")
            conn.execute("ALTER TABLE tasks ADD COLUMN solicitante TEXT")
    print("Migración v2 verificada.")


def migrate_db_v3():
    """Migración V3: Asegurar tabla technicians y columnas completed_by/at en tasks."""
    print("Verificando migración de DB v3...")
    with get_db_connection() as conn:
        if not _table_exists(conn, "technicians"):
            print("Creando tabla technicians...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS technicians (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )

        if not _column_exists(conn, "tasks", "completed_by"):
            print("Agregando col completed_by a tasks...")
            conn.execute("ALTER TABLE tasks ADD COLUMN completed_by TEXT")

        if not _column_exists(conn, "tasks", "completed_at"):
            print("Agregando col completed_at a tasks...")
            conn.execute("ALTER TABLE tasks ADD COLUMN completed_at DATETIME")

    print("Migración v3 verificada.")


def migrate_db_v4():
    """Migración V4: Asegurar columna 'categoria' en tasks."""
    print("Verificando migración de DB v4...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "tasks", "categoria"):
            print("Aplicando migración V4: Agregando 'categoria' a tasks...")
            conn.execute("ALTER TABLE tasks ADD COLUMN categoria TEXT")
    print("Migración v4 verificada.")


def migrate_db_v5():
    """Migración V5: Asegurar tabla audit_logs."""
    print("Verificando migración de DB v5...")
    with get_db_connection() as conn:
        if not _table_exists(conn, "audit_logs"):
            print("Creando tabla audit_logs...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    pc_name VARCHAR(255),
                    field VARCHAR(255),
                    old_value TEXT,
                    new_value TEXT,
                    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
    print("Migración v5 verificada.")


def migrate_db_v6():
    """Migración V6: Asegurar columna 'assigned_to' en tasks."""
    print("Verificando migración de DB v6...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "tasks", "assigned_to"):
            print("Aplicando migración V6: Agregando 'assigned_to' a tasks...")
            conn.execute("ALTER TABLE tasks ADD COLUMN assigned_to TEXT")
        else:
            print("Migración V6 verificada.")


def migrate_db_v7():
    """Migración V7: Asegurar columna 'fuero' en pcs."""
    print("Verificando migración de DB v7...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "pcs", "fuero"):
            print("Aplicando migración V7: Agregando 'fuero' a pcs...")
            conn.execute("ALTER TABLE pcs ADD COLUMN fuero TEXT")
        else:
            print("Migración V7 verificada.")


def migrate_db_v8():
    """Migración V8: Asegurar columna 'fuero' en tasks."""
    print("Verificando migración de DB v8...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "tasks", "fuero"):
            print("Aplicando migración V8: Agregando 'fuero' a tasks...")
            conn.execute("ALTER TABLE tasks ADD COLUMN fuero TEXT")
        else:
            print("Migración V8 verificada.")


def migrate_db_v9():
    """Migración V9: Agregar columnas de infraestructura de red y ubicación a pcs."""
    print("Verificando migración de DB v9...")
    new_columns = {
        "switch_name": "TEXT",
        "switch_port": "TEXT",
        "pachera_name": "TEXT",
        "pachera_port": "TEXT",
        "building": "TEXT",
        "floor": "TEXT"
    }
    with get_db_connection() as conn:
        for col, dtype in new_columns.items():
            if not _column_exists(conn, "pcs", col):
                print(f"Aplicando migración V9: Agregando '{col}' a pcs...")
                try:
                    conn.execute(f"ALTER TABLE pcs ADD COLUMN {col} {dtype}")
                except Exception as e:
                    print(f"Error agregando columna {col}: {e}")
    print("Migración V9 verificada.")


def migrate_db_v10():
    """Migración V10: Agregar columnas de alerta de salud a pcs."""
    print("Verificando migración de DB v10...")
    new_columns = {
        "alerta_disco": "TINYINT(1) DEFAULT 0",
        "alerta_uptime": "TINYINT(1) DEFAULT 0"
    }
    with get_db_connection() as conn:
        for col, dtype in new_columns.items():
            if not _column_exists(conn, "pcs", col):
                print(f"Aplicando migración V10: Agregando '{col}' a pcs...")
                try:
                    conn.execute(f"ALTER TABLE pcs ADD COLUMN {col} {dtype}")
                except Exception as e:
                    print(f"Error agregando columna {col}: {e}")
    print("Migración V10 verificada.")


def migrate_db_v11():
    """Migración V11: Asegurar tabla components."""
    print("Verificando migración de DB v11...")
    with get_db_connection() as conn:
        if not _table_exists(conn, "components"):
            print("Creando tabla components...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS components (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    serial_number VARCHAR(255) UNIQUE,
                    component_type VARCHAR(100) NOT NULL,
                    brand_model TEXT,
                    status VARCHAR(50) DEFAULT 'Stock',
                    assigned_pc VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (assigned_pc) REFERENCES pcs(pc_name) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
    print("Migración V11 verificada.")


def migrate_db_v12():
    """Migración V12: Asegurar columna 'assigned_to_component_id' en components."""
    print("Verificando migración de DB v12...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "components", "assigned_to_component_id"):
            print("Aplicando migración V12: Agregando 'assigned_to_component_id' a components...")
            conn.execute(
                "ALTER TABLE components ADD COLUMN assigned_to_component_id INT, "
                "ADD CONSTRAINT fk_comp_self FOREIGN KEY (assigned_to_component_id) REFERENCES components(id) ON DELETE SET NULL"
            )
        else:
            print("Migración V12 verificada.")


def migrate_db_v13():
    """Migración V13: Agregar supplier e invoice_number a components y ups_inventory."""
    print("Verificando migración de DB v13...")
    with get_db_connection() as conn:
        for table in ["components", "ups_inventory"]:
            if not _column_exists(conn, table, "supplier"):
                print(f"Aplicando migración V13: Agregando 'supplier' e 'invoice_number' a {table}...")
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN supplier TEXT")
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN invoice_number TEXT")
                except Exception as e:
                    print(f"Error agregando columnas a {table}: {e}")

        # Migrar tabla baterias_stock si aún existe
        if _table_exists(conn, "baterias_stock"):
            print("Aplicando migración V13: Migrando tabla baterias_stock hacia components...")
            baterias = conn.execute(
                "SELECT id, code, brand_model, status, created_at FROM baterias_stock"
            ).fetchall()

            status_map = {"Stock": "Stock", "Asignada": "Instalado", "Descartada": "Retirado"}

            for bat in baterias:
                existing_comp = conn.execute(
                    "SELECT id FROM components WHERE component_type='Batería UPS' AND serial_number=%s",
                    (bat["code"],)
                ).fetchone()

                if existing_comp:
                    new_comp_id = existing_comp["id"]
                else:
                    mapped_status = status_map.get(bat["status"], "Stock")
                    conn.execute(
                        """
                        INSERT INTO components (serial_number, component_type, brand_model, status, created_at)
                        VALUES (%s, 'Batería UPS', %s, %s, %s)
                        """,
                        (bat["code"], bat["brand_model"], mapped_status, bat["created_at"])
                    )
                    new_comp_id = conn.cursor.lastrowid

                conn.execute(
                    "UPDATE ups_inventory SET assigned_battery_id=%s WHERE assigned_battery_id=%s",
                    (new_comp_id, bat["id"])
                )

            try:
                conn.execute("RENAME TABLE baterias_stock TO baterias_stock_old")
            except Exception:
                pass

    print("Migración V13 verificada.")


def migrate_db_v14():
    """Migración V14: Asegurar tabla network_printers."""
    print("Verificando migración de DB v14...")
    with get_db_connection() as conn:
        if not _table_exists(conn, "network_printers"):
            print("Creando tabla network_printers...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS network_printers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ip_address VARCHAR(255),
                    serial_number VARCHAR(255) UNIQUE,
                    brand_model TEXT,
                    fuero TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            print("Migrando impresoras existentes...")
            # Migrar las impresoras que ya estuvieran en components
            printers = conn.execute("SELECT serial_number, brand_model, created_at FROM components WHERE component_type = 'Impresora'").fetchall()
            for p in printers:
                # Insertamos con IP vacía porque antes no se guardaba
                conn.execute(
                    "INSERT IGNORE INTO network_printers (ip_address, serial_number, brand_model, created_at) VALUES ('N/A', %s, %s, %s)",
                    (p['serial_number'], p['brand_model'], p['created_at'])
                )
            # Borrar las impresoras de components
            conn.execute("DELETE FROM components WHERE component_type = 'Impresora'")
    print("Migración V14 verificada.")


def migrate_db_v15():
    """Migración V15: Agregar alerta de nombre duplicado a pcs."""
    print("Verificando migración de DB v15...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "pcs", "alerta_nombre_duplicado"):
            print("Aplicando migración V15: Agregando 'alerta_nombre_duplicado' a pcs...")
            conn.execute("ALTER TABLE pcs ADD COLUMN alerta_nombre_duplicado TINYINT(1) DEFAULT 0")
        else:
            print("Migración V15 verificada.")




def migrate_db_v16():
    """Migración V16: Crear tabla pc_network_printers."""
    print("Verificando migración de DB v16...")
    with get_db_connection() as conn:
        if not _table_exists(conn, "pc_network_printers"):
            print("Creando tabla pc_network_printers...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pc_network_printers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    pc_name VARCHAR(255),
                    printer_id INT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pc_name) REFERENCES pcs(pc_name) ON DELETE CASCADE,
                    FOREIGN KEY (printer_id) REFERENCES network_printers(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
    print("Migración v16 verificada.")


def migrate_db_v17():
    """Migración V17: Asegurar columna 'phone' en ad_users."""
    print("Verificando migración de DB v17...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "ad_users", "phone"):
            print("Aplicando migración V17: Agregando 'phone' a ad_users...")
            conn.execute("ALTER TABLE ad_users ADD COLUMN phone TEXT")
        else:
            print("Migración V17 verificada.")


def migrate_db_v18():
    """Migración V18: Crear tabla fcm_tokens para Web Push / Firebase."""
    print("Verificando migración de DB v18...")
    with get_db_connection() as conn:
        if not _table_exists(conn, "fcm_tokens"):
            print("Creando tabla fcm_tokens...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fcm_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    technician_name VARCHAR(255) NOT NULL,
                    token TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_tech (technician_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
        else:
            print("Migración V18 verificada.")


def migrate_db_v19():
    """Migración V19: Crear tabla app_users para acceso al sistema."""
    print("Verificando migración de DB v19...")
    with get_db_connection() as conn:
        if not _table_exists(conn, "app_users"):
            print("Creando tabla app_users...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL UNIQUE,
                    display_name VARCHAR(255),
                    password_hash TEXT NOT NULL,
                    is_superuser TINYINT(1) DEFAULT 0,
                    is_active TINYINT(1) DEFAULT 1,
                    must_change_password TINYINT(1) DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
        else:
            print("Migración V19 verificada.")


def migrate_db_v20():
    """Migración V20: Roles y permisos de acceso para app_users."""
    print("Verificando migración de DB v20...")
    new_columns = {
        "role": "VARCHAR(50) DEFAULT 'tecnico'",
        "technician_name": "VARCHAR(255)",
        "can_access_dashboard": "TINYINT(1) DEFAULT 1",
        "can_access_mobile": "TINYINT(1) DEFAULT 1",
        "can_access_infrastructure": "TINYINT(1) DEFAULT 0",
        "can_access_reports": "TINYINT(1) DEFAULT 0",
    }

    with get_db_connection() as conn:
        for col, dtype in new_columns.items():
            if not _column_exists(conn, "app_users", col):
                print(f"Aplicando migración V20: Agregando '{col}' a app_users...")
                conn.execute(f"ALTER TABLE app_users ADD COLUMN {col} {dtype}")

        conn.execute(
            """
            UPDATE app_users
            SET role = CASE WHEN is_superuser = 1 THEN 'administrador' ELSE COALESCE(NULLIF(role, ''), 'tecnico') END,
                can_access_dashboard = CASE WHEN is_superuser = 1 THEN 1 ELSE can_access_dashboard END,
                can_access_mobile = CASE WHEN is_superuser = 1 THEN 1 ELSE can_access_mobile END,
                can_access_infrastructure = CASE WHEN is_superuser = 1 THEN 1 ELSE can_access_infrastructure END,
                can_access_reports = CASE WHEN is_superuser = 1 THEN 1 ELSE can_access_reports END
            """
        )
        conn.commit()

    print("Migración V20 verificada.")


def migrate_db_v21():
    """Migración V21: Asegurar columna 'printer_sn' en pcs."""
    print("Verificando migración de DB v21...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "pcs", "printer_sn"):
            print("Aplicando migración V21: Agregando 'printer_sn' a pcs...")
            conn.execute("ALTER TABLE pcs ADD COLUMN printer_sn TEXT")
        else:
            print("Migración V21 verificada.")


def migrate_db_v22():
    """Migración V22: Asegurar columna 'phone' en app_users."""
    print("Verificando migración de DB v22...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "app_users", "phone"):
            print("Aplicando migración V22: Agregando 'phone' a app_users...")
            conn.execute("ALTER TABLE app_users ADD COLUMN phone VARCHAR(255)")
        else:
            print("Migración V22 verificada.")


def migrate_db_v23():
    """Migración V23: Agregar fuero a ad_users."""
    print("Verificando migración de DB v23...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "ad_users", "fuero"):
            print("Aplicando migración V23: Agregando 'fuero' a ad_users...")
            conn.execute("ALTER TABLE ad_users ADD COLUMN fuero TEXT")
        else:
            print("Migración V23 verificada.")

def migrate_db_v24():
    """Migración V24: Agregar fuero a network_printers."""
    print("Verificando migración de DB v24...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "network_printers", "fuero"):
            print("Aplicando migración V24: Agregando 'fuero' a network_printers...")
            conn.execute("ALTER TABLE network_printers ADD COLUMN fuero TEXT")
        else:
            print("Migración V24 verificada.")


def migrate_db_v25():
    """Migración V25: Asegurar columnas user_name, action_type e ip_address en audit_logs."""
    print("Verificando migración de DB v25...")
    new_columns = {
        "user_name": "VARCHAR(255) DEFAULT 'SISTEMA'",
        "action_type": "VARCHAR(100) DEFAULT 'UPDATE'",
        "ip_address": "VARCHAR(100)"
    }
    with get_db_connection() as conn:
        for col, dtype in new_columns.items():
            if not _column_exists(conn, "audit_logs", col):
                print(f"Aplicando migración V25: Agregando '{col}' a audit_logs...")
                conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col} {dtype}")
    print("Migración V25 verificada.")
    
def migrate_db_v26():
    """Migración V26: Asegurar columna 'mac_address' en pcs."""
    print("Verificando migración de DB v26...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "pcs", "mac_address"):
            print("Aplicando migración V26: Agregando 'mac_address' a pcs...")
            conn.execute("ALTER TABLE pcs ADD COLUMN mac_address VARCHAR(100)")
        else:
            print("Migración V26 verificada.")


def migrate_db_v27():
    """Migración V27: agregar índices operativos para dashboard, tareas y auditoría."""
    print("Verificando migración de DB v27...")
    indexes = [
        ("pcs", "idx_pcs_active_name", "CREATE INDEX idx_pcs_active_name ON pcs (is_active, pc_name(100))"),
        ("tasks", "idx_tasks_pc_estado", "CREATE INDEX idx_tasks_pc_estado ON tasks (pc_name(100), estado(30))"),
        ("tasks", "idx_tasks_estado_completed", "CREATE INDEX idx_tasks_estado_completed ON tasks (estado(30), completed_at)"),
        ("audit_logs", "idx_audit_logs_pc_changed", "CREATE INDEX idx_audit_logs_pc_changed ON audit_logs (pc_name(100), changed_at)"),
    ]
    with get_db_connection() as conn:
        for table, index_name, ddl in indexes:
            if _table_exists(conn, table) and not _index_exists(conn, table, index_name):
                print(f"Aplicando migración V27: creando índice '{index_name}'...")
                conn.execute(ddl)
    print("Migración V27 verificada.")


def migrate_db_v28():
    """Migración V28: crear auditoría administrativa para gestión de usuarios."""
    print("Verificando migración de DB v28...")
    with get_db_connection() as conn:
        if not _table_exists(conn, "admin_audit_logs"):
            print("Aplicando migración V28: creando tabla admin_audit_logs...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_audit_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    action_type VARCHAR(100) NOT NULL,
                    actor_username VARCHAR(255),
                    target_username VARCHAR(255),
                    ip_address VARCHAR(100),
                    details LONGTEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
        if not _index_exists(conn, "admin_audit_logs", "idx_admin_audit_created"):
            print("Aplicando migración V28: creando índice idx_admin_audit_created...")
            conn.execute("CREATE INDEX idx_admin_audit_created ON admin_audit_logs (created_at)")
    print("Migración V28 verificada.")


def migrate_db_v29():
    """Migración V29: Categorización de tareas en tipos (Incidente, Tarea, Riesgo) e Impacto."""
    print("Verificando migración de DB v29...")
    new_columns = {
        "tipo_actividad": "VARCHAR(50) DEFAULT 'tarea'",  # 'incidente', 'tarea', 'riesgo', 'mantenimiento'
        "prioridad": "INT DEFAULT 1",                    # 1: Baja, 2: Media, 3: Alta, 4: Crítica
        "impacto_valor": "INT DEFAULT 1",                # Escala de impacto en el negocio
        "resumen_impacto": "TEXT"                        # Texto explicativo del porqué del impacto
    }
    with get_db_connection() as conn:
        for col, dtype in new_columns.items():
            if not _column_exists(conn, "tasks", col):
                print(f"Aplicando migración V29: Agregando '{col}' a tasks...")
                conn.execute(f"ALTER TABLE tasks ADD COLUMN {col} {dtype}")
    print("Migración V29 verificada.")


def migrate_db_v30():
    """MigraciÃ³n V30: catÃ¡logo administrable de prefijos de fuero."""
    print("Verificando migraciÃ³n de DB v30...")
    with get_db_connection() as conn:
        if not _table_exists(conn, "fuero_mappings"):
            print("Aplicando migraciÃ³n V30: creando tabla fuero_mappings...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fuero_mappings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    prefix_code VARCHAR(100) NOT NULL UNIQUE,
                    fuero_label VARCHAR(255) NOT NULL,
                    notes TEXT,
                    is_active TINYINT(1) DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )

        if not _index_exists(conn, "fuero_mappings", "idx_fuero_mappings_active_prefix"):
            print("Aplicando migraciÃ³n V30: creando Ã­ndice idx_fuero_mappings_active_prefix...")
            conn.execute(
                "CREATE INDEX idx_fuero_mappings_active_prefix ON fuero_mappings (is_active, prefix_code)"
            )

        existing = conn.execute("SELECT COUNT(*) AS cnt FROM fuero_mappings").fetchone()
        if not existing or not existing["cnt"]:
            print("Aplicando migraciÃ³n V30: sembrando catÃ¡logo inicial de fueros...")
            for prefix, label in DEFAULT_FUERO_MAPPING.items():
                conn.execute(
                    """
                    INSERT INTO fuero_mappings (prefix_code, fuero_label, is_active)
                    VALUES (%s, %s, 1)
                    ON DUPLICATE KEY UPDATE
                        fuero_label = VALUES(fuero_label),
                        is_active = VALUES(is_active)
                    """,
                    (prefix, label),
                )
    print("MigraciÃ³n V30 verificada.")


def run_all_migrations():
    """Ejecuta todas las migraciones en orden."""
    migrate_db_v2()
    migrate_db_v3()
    migrate_db_v4()
    migrate_db_v5()
    migrate_db_v6()
    migrate_db_v7()
    migrate_db_v8()
    migrate_db_v9()
    migrate_db_v10()
    migrate_db_v11()
    migrate_db_v12()
    migrate_db_v13()
    migrate_db_v14()
    migrate_db_v15()
    migrate_db_v16()
    migrate_db_v17()
    migrate_db_v18()
    migrate_db_v19()
    migrate_db_v20()
    migrate_db_v21()
    migrate_db_v22()
    migrate_db_v23()
    migrate_db_v24()
    migrate_db_v25()
    migrate_db_v26()
    migrate_db_v27()
    migrate_db_v28()
    migrate_db_v29()
    migrate_db_v30()
    migrate_db_v31()
    migrate_db_v33()
    migrate_db_v34()
    migrate_db_v35()
    migrate_db_v36()
    migrate_db_v37()
    migrate_db_v38()
    migrate_db_v39()
    with get_db_connection() as conn:
        migration_v32(conn)

def migrate_db_v33():
    """Migración V33: Permiso de acceso para Operadores Telefónicos."""
    print("Verificando migración de DB v33...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "app_users", "can_access_operadores"):
            print("Aplicando migración V33: Agregando 'can_access_operadores' a app_users...")
            conn.execute("ALTER TABLE app_users ADD COLUMN can_access_operadores TINYINT(1) DEFAULT 0")
    print("Migración V33 verificada.")

def migrate_db_v34():
    """MigraciÃ³n V34: normalizar tareas sin PC hacia 'PC Generica'."""
    print("Verificando migraciÃ³n de DB v34...")
    with get_db_connection() as conn:
        generic_pc = conn.execute(
            "SELECT 1 FROM pcs WHERE pc_name = 'PC Generica' LIMIT 1"
        ).fetchone()
        if not generic_pc:
            print("Aplicando migraciÃ³n V34: creando 'PC Generica' faltante...")
            conn.execute(
                """
                INSERT INTO pcs (pc_name, os_name, is_active)
                VALUES ('PC Generica', 'Virtual/Pendiente', 'True')
                """
            )

        updated = conn.execute(
            """
            UPDATE tasks
            SET pc_name = 'PC Generica'
            WHERE pc_name IS NULL OR TRIM(pc_name) = ''
            """
        )
        print(f"MigraciÃ³n V34 verificada. Tareas normalizadas: {updated.rowcount}")

def migrate_db_v31():
    """Migración V31: Infraestructura de Planos y Coordenadas."""
    print("Verificando migración de DB v31...")
    with get_db_connection() as conn:
        # 1. Crear tabla de planos
        if not _table_exists(conn, "infrastructure_maps"):
            print("Aplicando migración V31: creando tabla infrastructure_maps...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS infrastructure_maps (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    image_url TEXT NOT NULL,
                    building VARCHAR(100),
                    floor VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )

        # 2. Añadir campos a PCs
        new_pc_cols = {
            "x_pos": "FLOAT DEFAULT 0",
            "y_pos": "FLOAT DEFAULT 0",
            "map_id": "INT"
        }
        for col, dtype in new_pc_cols.items():
            if not _column_exists(conn, "pcs", col):
                print(f"Agregando '{col}' a pcs...")
                conn.execute(f"ALTER TABLE pcs ADD COLUMN {col} {dtype}")
        
        # Foreign Key para map_id en pcs (si no existe)
        try:
            conn.execute("ALTER TABLE pcs ADD CONSTRAINT fk_pcs_map FOREIGN KEY (map_id) REFERENCES infrastructure_maps(id) ON DELETE SET NULL")
        except Exception: pass

        # 3. Añadir campos a Impresoras de Red
        new_prn_cols = {
            "x_pos": "FLOAT DEFAULT 0",
            "y_pos": "FLOAT DEFAULT 0",
            "map_id": "INT"
        }
        for col, dtype in new_prn_cols.items():
            if not _column_exists(conn, "network_printers", col):
                print(f"Agregando '{col}' a network_printers...")
                conn.execute(f"ALTER TABLE network_printers ADD COLUMN {col} {dtype}")

        # Foreign Key para map_id en printers
        try:
            conn.execute("ALTER TABLE network_printers ADD CONSTRAINT fk_prn_map FOREIGN KEY (map_id) REFERENCES infrastructure_maps(id) ON DELETE SET NULL")
        except Exception: pass

    print("Migración V31 verificada.")

def migration_v32(conn):
    """Agrega campos de posición a usuarios (ad_users) para mapas topológicos."""
    print("Verificando Migración V32 (Posiciones de Usuarios)...")
    new_user_cols = {
        "x_pos": "FLOAT DEFAULT 0",
        "y_pos": "FLOAT DEFAULT 0",
        "map_id": "INT"
    }
    for col, dtype in new_user_cols.items():
        if not _column_exists(conn, "ad_users", col):
            print(f"Agregando '{col}' a ad_users...")
            conn.execute(f"ALTER TABLE ad_users ADD COLUMN {col} {dtype}")
    
    # Foreign Key
    try:
        conn.execute("ALTER TABLE ad_users ADD CONSTRAINT fk_user_map FOREIGN KEY (map_id) REFERENCES infrastructure_maps(id) ON DELETE SET NULL")
    except Exception: pass
    
    print("Migración V32 verificada.")

def migrate_db_v35():
    """Migración V35: Asegurar columna 'solucion' en tasks."""
    print("Verificando migración de DB v35...")
    with get_db_connection() as conn:
        if not _column_exists(conn, "tasks", "solucion"):
            print("Aplicando migración V35: Agregando 'solucion' a tasks...")
            conn.execute("ALTER TABLE tasks ADD COLUMN solucion TEXT")
    print("Migración v35 verificada.")

def migrate_db_v36():
    """Migración V36: Crear tabla task_actions para el historial de tareas."""
    print("Verificando migración de DB v36...")
    with get_db_connection() as conn:
        if not _table_exists(conn, "task_actions"):
            print("Aplicando migración V36: creando tabla task_actions...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_actions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    task_id INT NOT NULL,
                    user_name VARCHAR(255) NOT NULL,
                    action_text TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            print("Creando índice para task_actions...")
            conn.execute("CREATE INDEX idx_task_actions_task_id ON task_actions (task_id)")
    print("Migración V36 verificada.")


def migrate_db_v37():
    """Migración V37: Crear tabla efemerides y cargar datos iniciales."""
    print("Verificando migración de DB v37...")
    with get_db_connection() as conn:
        if not _table_exists(conn, "efemerides"):
            print("Aplicando migración V37: creando tabla efemerides...")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS efemerides (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    dia_mes VARCHAR(5) NOT NULL,
                    titulo VARCHAR(255) NOT NULL,
                    descripcion TEXT,
                    icono VARCHAR(10) DEFAULT '🇦🇷',
                    is_active TINYINT(1) DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            
            # Carga inicial
            efemerides_seed = [
                ('03-24', 'Día Nacional de la Memoria por la Verdad y la Justicia', 'Feriado inamovible en Argentina.', '🕊️'),
                ('04-02', 'Día del Veterano y de los Caídos en la Guerra de Malvinas', 'Homenaje a los caídos y veteranos de la guerra de 1982.', '🇦🇷'),
                ('05-01', 'Día del Trabajador', 'Celebración mundial del movimiento obrero.', '👷'),
                ('05-25', '¡Semana de Mayo! 🇦🇷', 'Conmemoración de la Revolución de Mayo de 1810.', '🇦🇷'),
                ('06-20', 'Día de la Bandera', 'En conmemoración del paso a la inmortalidad de Manuel Belgrano.', '🇦🇷'),
                ('07-09', 'Día de la Independencia', 'Declaración de la independencia en 1816 en Tucumán.', '🇦🇷'),
                ('08-17', 'Paso a la Inmortalidad del Gral. José de San Martín', 'Homenaje al Libertador de América.', '🐎'),
                ('09-11', 'Día del Maestro', 'En conmemoración del fallecimiento de Domingo Faustino Sarmiento.', '📚'),
                ('09-21', 'Día del Estudiante / Primavera', 'Comienzo de la primavera y celebración de los estudiantes.', '🌸'),
                ('10-12', 'Día del Respeto a la Diversidad Cultural', 'Conmemoración del encuentro de culturas y respeto a la diversidad.', '🌎'),
                ('11-20', 'Día de la Soberanía Nacional', 'Batalla de la Vuelta de Obligado.', '⚓'),
                ('12-08', 'Inmaculada Concepción de María', 'Feriado religioso.', '✝️'),
                ('12-25', 'Navidad', 'Celebración de Navidad.', '🎄'),
                ('12-31', 'Fin de Año', '¡Feliz año nuevo!', '🥂')
            ]
            
            for dia_mes, titulo, desc, icono in efemerides_seed:
                conn.execute(
                    "INSERT INTO efemerides (dia_mes, titulo, descripcion, icono, is_active) VALUES (%s, %s, %s, %s, 0)",
                    (dia_mes, titulo, desc, icono)
                )
    print("Migración V37 verificada.")


def migrate_db_v38():
    """Migración V38: Semilla extendida de efemérides (Internacionales e Informáticas)."""
    print("Verificando migración de DB v38...")
    with get_db_connection() as conn:
        if _table_exists(conn, "efemerides"):
            # Chequeamos si ya se insertó una de las efemérides nuevas para no duplicar
            existing = conn.execute("SELECT id FROM efemerides WHERE titulo = 'Día del Programador'").fetchone()
            if not existing:
                print("Aplicando migración V38: insertando semilla extendida de efemérides...")
                efemerides_seed_v38 = [
                    ('01-01', 'Año Nuevo', '¡Feliz y próspero Año Nuevo!', '🎆'),
                    ('01-28', 'Día de la Privacidad de la Información', 'Concientización sobre la protección de datos.', '🔐'),
                    ('02-14', 'Día de San Valentín', 'Día del amor y la amistad.', '❤️'),
                    ('03-08', 'Día Internacional de la Mujer', 'En conmemoración a la lucha por la igualdad.', '👩'),
                    ('03-31', 'World Backup Day', 'Día Mundial de la Copia de Seguridad. ¡Verifica tus respaldos!', '💾'),
                    ('04-22', 'Día de la Tierra', 'Protejamos nuestro planeta.', '🌍'),
                    ('05-17', 'Día de Internet', 'Día Mundial de las Telecomunicaciones y la Sociedad de la Información.', '🌐'),
                    ('06-05', 'Día del Medio Ambiente', 'Concientización global sobre el cuidado del medio ambiente.', '🌱'),
                    ('07-20', 'Día del Amigo', 'Celebración de la amistad.', '🤝'),
                    ('09-13', 'Día del Programador', 'En el día 256 del año, celebramos a los creadores de código.', '💻'),
                    ('10-31', 'Halloween', '¡Feliz Noche de Brujas!', '🎃'),
                    ('11-30', 'Día Internacional de la Seguridad Informática', 'Protege tus contraseñas y tu infraestructura.', '🛡️'),
                    ('12-24', 'Nochebuena', 'Víspera de Navidad.', '⭐')
                ]
                
                for dia_mes, titulo, desc, icono in efemerides_seed_v38:
                    conn.execute(
                        "INSERT INTO efemerides (dia_mes, titulo, descripcion, icono, is_active) VALUES (%s, %s, %s, %s, 0)",
                        (dia_mes, titulo, desc, icono)
                    )
    print("Migración V38 verificada.")

def migrate_db_v39():
    """Migración V39: Semilla gigante de efemérides para rellenar días vacíos."""
    print("Verificando migración de DB v39...")
    with get_db_connection() as conn:
        if _table_exists(conn, "efemerides"):
            existing = conn.execute("SELECT id FROM efemerides WHERE titulo = 'Día del Trabajador del Estado'").fetchone()
            if not existing:
                print("Aplicando migración V39: insertando semilla gigante de efemérides...")
                efemerides_seed_v39 = [
                    ('01-06', 'Día de Reyes', 'Llegada de los Reyes Magos.', '👑'),
                    ('02-24', 'Día del Mecánico', 'Homenaje a los mecánicos y trabajadores automotrices.', '🔧'),
                    ('03-22', 'Día Mundial del Agua', 'Concientización sobre la importancia del agua dulce.', '💧'),
                    ('04-07', 'Día Mundial de la Salud', 'Celebración de la OMS y concientización sobre la salud.', '🏥'),
                    ('04-23', 'Día Internacional del Libro', 'Día mundial de la lectura y los derechos de autor.', '📖'),
                    ('05-15', 'Día Internacional de la Familia', 'Celebración de las familias en todo el mundo.', '👨‍👩‍👧‍👦'),
                    ('06-27', 'Día del Trabajador del Estado', 'Día de descanso para la administración pública.', '🏛️'),
                    ('07-28', 'Día de la Gendarmería Nacional', 'Aniversario de la creación de la Gendarmería Argentina.', '👮'),
                    ('08-12', 'Día del Trabajador de Televisión', 'Día del empleado de la televisión, telecomunicaciones y datos.', '📺'),
                    ('08-29', 'Día del Abogado', 'En homenaje a Juan Bautista Alberdi.', '⚖️'),
                    ('09-04', 'Día de la Secretaria', 'Homenaje a las secretarias y administrativos.', '📝'),
                    ('09-28', 'Día Internacional del Derecho a Saber', 'Acceso a la información pública.', '🔍'),
                    ('10-01', 'Día Internacional del Café', '¡Disfruta de una buena taza de café mientras programas!', '☕'),
                    ('10-24', 'Día de las Naciones Unidas', 'Día de las Naciones Unidas (ONU).', '🇺🇳'),
                    ('11-06', 'Día de los Parques Nacionales', 'Aniversario de los Parques Nacionales Argentinos.', '🏞️'),
                    ('11-10', 'Día de la Tradición', 'En homenaje a José Hernández, autor del Martín Fierro.', '🧉'),
                    ('12-10', 'Día de los Derechos Humanos', 'Declaración Universal de los Derechos Humanos.', '🕊️'),
                    ('01-15', 'Wikipedia Day', 'Día en que se lanzó Wikipedia.', '🌐'),
                    ('04-04', 'Día del Error 404', '¡Página no encontrada!', '🚫'),
                    ('05-04', 'Star Wars Day', 'May the 4th be with you.', '🛸'),
                    ('05-25', 'Geek Pride Day', 'Día del Orgullo Friki / Towel Day.', '🤓'),
                    ('07-17', 'World Emoji Day', 'Día Mundial del Emoji.', '😃'),
                    ('10-18', 'Día Mundial de la Protección de la Naturaleza', 'A cuidar el entorno natural.', '🌲')
                ]
                
                for dia_mes, titulo, desc, icono in efemerides_seed_v39:
                    # check for duplicates just in case
                    dup = conn.execute("SELECT id FROM efemerides WHERE dia_mes = %s AND titulo = %s", (dia_mes, titulo)).fetchone()
                    if not dup:
                        conn.execute(
                            "INSERT INTO efemerides (dia_mes, titulo, descripcion, icono, is_active) VALUES (%s, %s, %s, %s, 0)",
                            (dia_mes, titulo, desc, icono)
                        )
    print("Migración V39 verificada.")

