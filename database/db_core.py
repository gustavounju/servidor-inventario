import pymysql
import pymysql.cursors
import os
import logging
from dotenv import load_dotenv
from utils.constants import DEFAULT_FUERO_MAPPING
from dbutils.pooled_db import PooledDB

load_dotenv()


class DBConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn
        self._cursor = None

    def execute(self, query, vars=None):
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception:
                pass
        self._cursor = self.conn.cursor()
        self._cursor.execute(query, vars)
        return self._cursor

    @property
    def cursor(self):
        """Acceso directo al último cursor (para lastrowid, rowcount, etc.)."""
        return self._cursor

    def fetchone(self):
        return self._cursor.fetchone() if self._cursor else None

    def fetchall(self):
        return self._cursor.fetchall() if self._cursor else []

    def commit(self):
        self.conn.commit()
        try:
            from servidor import invalidate_global_cache
            invalidate_global_cache()
        except ImportError:
            pass

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception:
                pass
        try:
            self.conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()


_DB_POOL = None

def _get_pool():
    global _DB_POOL
    if _DB_POOL is not None:
        return _DB_POOL
    host = os.environ.get("DB_HOST", "127.0.0.1")
    user = os.environ.get("DB_USER", "root")
    password = os.environ.get("DB_PASS", "")
    dbname = os.environ.get("DB_NAME", "inventario_dev")
    port = int(os.environ.get("DB_PORT", "3306"))
    session_time_zone = os.environ.get("DB_TIME_ZONE", "-03:00")

    _DB_POOL = PooledDB(
        creator=pymysql,
        mincached=2,
        maxcached=10,
        maxconnections=20,
        blocking=True,
        host=host,
        user=user,
        password=password,
        database=dbname,
        port=port,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=10,
        init_command=f"SET time_zone = '{session_time_zone}'"
    )
    return _DB_POOL

def get_db_connection():
    """Obtiene una conexión del pool. Siempre usar con 'with': with get_db_connection() as conn."""
    conn = _get_pool().connection()
    return DBConnectionWrapper(conn)


def init_db():
    print("Inicializando base de datos MySQL...")
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pcs (
                pc_name VARCHAR(255) PRIMARY KEY,
                os_name TEXT,
                processor TEXT,
                ram_gb FLOAT,
                ip_address TEXT,
                last_user TEXT,
                last_report DATETIME,
                ram_detalles TEXT,
                disk_models TEXT,
                disk_speeds_rpm TEXT,
                motherboard_model TEXT,
                monitors TEXT,
                printer_model TEXT,
                printer_port TEXT,
                printer_sn TEXT,
                ping_ms TEXT,
                ping_loss_pct TEXT,
                alerta_ram_baja TINYINT(1) DEFAULT 0,
                alerta_sin_impresora TINYINT(1) DEFAULT 0,
                alerta_impresora_red TINYINT(1) DEFAULT 0,
                is_active TINYINT(1) DEFAULT 1,
                full_json_data LONGTEXT,
                fuero TEXT,
                switch_name TEXT,
                switch_port TEXT,
                pachera_name TEXT,
                pachera_port TEXT,
                building TEXT,
                floor TEXT,
                alerta_disco TINYINT(1) DEFAULT 0,
                alerta_uptime TINYINT(1) DEFAULT 0,
                alerta_nombre_duplicado TINYINT(1) DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pc_name VARCHAR(255),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                descripcion TEXT NOT NULL,
                estado VARCHAR(50) NOT NULL DEFAULT 'Pendiente',
                solicitante TEXT,
                completed_by TEXT,
                completed_at DATETIME,
                categoria TEXT,
                assigned_to TEXT,
                fuero TEXT,
                tipo_actividad VARCHAR(50) DEFAULT 'tarea',
                prioridad INT DEFAULT 1,
                impacto_valor INT DEFAULT 1,
                resumen_impacto TEXT,
                solucion TEXT,
                is_edited TINYINT(1) DEFAULT 0,
                desc_edited TINYINT(1) DEFAULT 0,
                sol_edited TINYINT(1) DEFAULT 0,
                FOREIGN KEY (pc_name) REFERENCES pcs(pc_name) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS pc_detected_printers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pc_name VARCHAR(255),
                printer_model TEXT,
                printer_port TEXT,
                printer_sn TEXT,
                is_ignored TINYINT(1) DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (pc_name) REFERENCES pcs(pc_name) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS technicians (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Intentar añadir columna office_version si no existe (Migración automática)
        try:
            conn.execute("ALTER TABLE pcs ADD COLUMN office_version TEXT AFTER printer_sn")
            print("Migración: Columna 'office_version' añadida exitosamente.")
        except Exception as e:
            logging.debug(f"Columna office_version ya existe o error menor: {e}")

        # Intentar añadir columna is_edited, desc_edited y sol_edited en tasks
        try:
            conn.execute("ALTER TABLE tasks ADD COLUMN is_edited TINYINT(1) DEFAULT 0 AFTER solucion")
        except Exception: pass
        try:
            conn.execute("ALTER TABLE tasks ADD COLUMN desc_edited TINYINT(1) DEFAULT 0 AFTER is_edited")
            conn.execute("ALTER TABLE tasks ADD COLUMN sol_edited TINYINT(1) DEFAULT 0 AFTER desc_edited")
            print("Migración: Columnas 'desc_edited' y 'sol_edited' añadidas exitosamente.")
        except Exception as e:
            logging.debug(f"Columnas editadas ya existen o error menor: {e}")

        # Intentar añadir columna can_audit_racks si no existe
        try:
            conn.execute("ALTER TABLE app_users ADD COLUMN can_audit_racks TINYINT(1) DEFAULT 0 AFTER can_access_reports")
            print("Migración: Columna 'can_audit_racks' añadida exitosamente.")
        except Exception as e:
            logging.debug(f"Columna can_audit_racks ya existe o error menor: {e}")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS components (
                id INT AUTO_INCREMENT PRIMARY KEY,
                serial_number VARCHAR(255) UNIQUE,
                component_type VARCHAR(100) NOT NULL,
                brand_model TEXT,
                status VARCHAR(50) DEFAULT 'Stock',
                assigned_pc VARCHAR(255),
                assigned_to_component_id INT,
                supplier TEXT,
                invoice_number TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assigned_pc) REFERENCES pcs(pc_name) ON DELETE SET NULL,
                FOREIGN KEY (assigned_to_component_id) REFERENCES components(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pc_name VARCHAR(255),
                field VARCHAR(255),
                old_value TEXT,
                new_value TEXT,
                user_name VARCHAR(255) DEFAULT 'SISTEMA',
                action_type VARCHAR(100) DEFAULT 'UPDATE',
                ip_address VARCHAR(100),
                changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ups_inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(255) UNIQUE NOT NULL,
                model VARCHAR(255) DEFAULT 'LYONN CTB-800V',
                supplier TEXT,
                invoice_number TEXT,
                assigned_pc VARCHAR(255),
                assigned_battery_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assigned_pc) REFERENCES pcs(pc_name) ON DELETE SET NULL,
                FOREIGN KEY (assigned_battery_id) REFERENCES components(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ad_users (
                username VARCHAR(255) PRIMARY KEY,
                real_name TEXT,
                phone TEXT,
                fuero TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS fuero_mappings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                prefix_code VARCHAR(100) NOT NULL UNIQUE,
                fuero_label VARCHAR(255) NOT NULL,
                notes TEXT,
                is_active TINYINT(1) DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        for prefix, label in DEFAULT_FUERO_MAPPING.items():
            conn.execute(
                """
                INSERT IGNORE INTO fuero_mappings (prefix_code, fuero_label, is_active)
                VALUES (%s, %s, 1)
                """,
                (prefix, label),
            )


        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title TEXT,
                body TEXT,
                url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                display_name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'tecnico',
                technician_name VARCHAR(255),
                password_hash TEXT NOT NULL,
                is_superuser TINYINT(1) DEFAULT 0,
                is_active TINYINT(1) DEFAULT 1,
                must_change_password TINYINT(1) DEFAULT 0,
                can_access_dashboard TINYINT(1) DEFAULT 1,
                can_access_mobile TINYINT(1) DEFAULT 1,
                can_access_infrastructure TINYINT(1) DEFAULT 0,
                can_access_reports TINYINT(1) DEFAULT 0,
                can_audit_racks TINYINT(1) DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS racks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL UNIQUE,
                ubicacion VARCHAR(100)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Seed default racks
        default_racks = ['Rack Central', 'Piso 1', 'Piso 2', 'Backup', 'Familia', 'Residual', 'Biblioteca']
        for rack in default_racks:
            conn.execute("INSERT IGNORE INTO racks (nombre, ubicacion) VALUES (%s, '')", (rack,))

        conn.execute("""
            CREATE TABLE IF NOT EXISTS rack_audits (
                id INT AUTO_INCREMENT PRIMARY KEY,
                rack_id INT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                estado_luces_bool TINYINT(1) DEFAULT 1,
                limpieza_ok_bool TINYINT(1) DEFAULT 1,
                iluminacion_ok_bool TINYINT(1) DEFAULT 1,
                temperatura_celsius_float FLOAT,
                observaciones_text TEXT,
                ruta_foto_text TEXT,
                tecnico VARCHAR(255),
                FOREIGN KEY (rack_id) REFERENCES racks(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Intentar añadir columna iluminacion_ok_bool si no existe
        try:
            conn.execute("ALTER TABLE rack_audits ADD COLUMN iluminacion_ok_bool TINYINT(1) DEFAULT 1 AFTER limpieza_ok_bool")
            print("Migración: Columna 'iluminacion_ok_bool' añadida exitosamente.")
        except Exception as e:
            logging.debug(f"Columna iluminacion_ok_bool ya existe o error menor: {e}")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS switches (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo_qr VARCHAR(100) UNIQUE NOT NULL,
                nombre VARCHAR(100) NOT NULL,
                marca VARCHAR(100),
                modelo VARCHAR(100),
                edificio VARCHAR(100),
                lugar VARCHAR(100),
                puertos_totales INT DEFAULT 0,
                puertos_poe INT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS switch_audits (
                id INT AUTO_INCREMENT PRIMARY KEY,
                switch_id INT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                estado_general VARCHAR(50) DEFAULT 'Online',
                puertos_libres INT DEFAULT 0,
                puertos_ocupados INT DEFAULT 0,
                puertos_fallados INT DEFAULT 0,
                observaciones_text TEXT,
                tecnico VARCHAR(255),
                FOREIGN KEY (switch_id) REFERENCES switches(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Migración de is_active VARCHAR('True'/'False') -> TINYINT(1)
        try:
            # Primero convertir los valores string que venían del sistema anterior
            conn.execute("UPDATE pcs SET is_active = 1 WHERE TRIM(is_active) IN ('True', 'true', '1')")
            conn.execute("UPDATE pcs SET is_active = 0 WHERE TRIM(is_active) IN ('False', 'false', '0')")
            # Luego cambiar el tipo de columna
            conn.execute("ALTER TABLE pcs MODIFY COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1")
            logging.info("Migración is_active completada: columna convertida a TINYINT(1).")
        except Exception as e:
            # Es normal que falle si ya está migrada (columna ya es TINYINT)
            logging.debug(f"Migración is_active ya aplicada o error menor: {e}")

    print("Base de datos lista y estructura verificada.")
