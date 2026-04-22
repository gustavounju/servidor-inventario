from database.db_core import get_db_connection
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
