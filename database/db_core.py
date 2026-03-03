import pymysql
import pymysql.cursors
import os
from dotenv import load_dotenv

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


def get_db_connection():
    host = os.environ.get("DB_HOST", "127.0.0.1")
    user = os.environ.get("DB_USER", "root")
    password = os.environ.get("DB_PASS", "")
    dbname = os.environ.get("DB_NAME", "inventario_dev")
    port = int(os.environ.get("DB_PORT", "3306"))

    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=dbname,
        port=port,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=10,
    )
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
                ping_ms TEXT,
                ping_loss_pct TEXT,
                alerta_ram_baja TINYINT(1) DEFAULT 0,
                alerta_sin_impresora TINYINT(1) DEFAULT 0,
                alerta_impresora_red TINYINT(1) DEFAULT 0,
                is_active VARCHAR(5) DEFAULT 'True',
                full_json_data LONGTEXT,
                fuero TEXT,
                switch_name TEXT,
                switch_port TEXT,
                pachera_name TEXT,
                pachera_port TEXT,
                building TEXT,
                floor TEXT,
                alerta_disco TINYINT(1) DEFAULT 0,
                alerta_uptime TINYINT(1) DEFAULT 0
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
                FOREIGN KEY (pc_name) REFERENCES pcs(pc_name) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS technicians (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

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
                real_name TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

    print("Base de datos lista y estructura verificada.")
