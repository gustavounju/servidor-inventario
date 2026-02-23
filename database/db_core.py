import sqlite3
import os

DB_FILE = "inventario.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crea tabla pcs y tabla tasks con todas las columnas necesarias."""
    print(f"Inicializando base de datos en '{DB_FILE}'...")
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pcs (
                pc_name TEXT PRIMARY KEY,
                os_name TEXT,
                processor TEXT,
                ram_gb REAL,
                ip_address TEXT,
                last_user TEXT,
                last_report TEXT,
                ram_detalles TEXT,
                disk_models TEXT,
                disk_speeds_rpm TEXT,
                motherboard_model TEXT,
                monitors TEXT,
                printer_model TEXT,
                printer_port TEXT,
                ping_ms TEXT,
                ping_loss_pct TEXT,
                alerta_ram_baja INTEGER DEFAULT 0,
                alerta_sin_impresora INTEGER DEFAULT 0,
                alerta_impresora_red INTEGER DEFAULT 0,
                is_active TEXT DEFAULT 'True',
                full_json_data TEXT,
                fuero TEXT,
                switch_name TEXT,
                switch_port TEXT,
                pachera_name TEXT,
                pachera_port TEXT,
                building TEXT,
                floor TEXT,
                alerta_disco INTEGER DEFAULT 0,
                alerta_uptime INTEGER DEFAULT 0
            ) 
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pc_name TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now', '-3 hours')),
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'Pendiente',
                solicitante TEXT,
                completed_by TEXT,
                completed_at TEXT,
                categoria TEXT,
                assigned_to TEXT,
                fuero TEXT,
                FOREIGN KEY (pc_name) REFERENCES pcs(pc_name)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS technicians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number TEXT UNIQUE,
                component_type TEXT NOT NULL,
                brand_model TEXT,
                status TEXT DEFAULT 'Stock', -- Stock, Instalado, Retirado
                assigned_pc TEXT,
                created_at TEXT DEFAULT (datetime('now', '-3 hours')),
                FOREIGN KEY (assigned_pc) REFERENCES pcs(pc_name)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pc_name TEXT,
                field TEXT,
                old_value TEXT,
                new_value TEXT,
                changed_at DATETIME DEFAULT (datetime('now', '-3 hours'))
            )
            """
        )

        conn.commit()
    print("Base de datos lista y estructura verificada.")
