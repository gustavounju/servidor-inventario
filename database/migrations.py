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
    print("Migración V16 verificada.")


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
