import os
import glob
import logging
import pymysql
from database.db_core import get_db_connection

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")

def init_migrations_table(conn):
    """Crea la tabla de migraciones si no existe."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    conn.commit()

def get_applied_migrations(conn):
    """Retorna un set con los nombres de las migraciones ya aplicadas."""
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row["version"] for row in rows}

def execute_sql_script(conn, file_path):
    """Ejecuta un script SQL separando por punto y coma."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Separación simple por punto y coma. 
    # Cuidado: no soporta punto y coma dentro de literales de cadena.
    # Dado que son scripts controlados, sirve para el propósito inicial.
    statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]

    for stmt in statements:
        # Evitar fallos si es solo un comentario
        if not stmt or stmt.startswith("--") and "\n" not in stmt:
            continue
        try:
            conn.execute(stmt)
        except Exception as e:
            logger.error(f"Error ejecutando statement en {file_path}:\n{stmt}\nError: {e}")
            raise

def run_migrations():
    """Busca scripts en database/migrations y aplica los pendientes."""
    if not os.path.exists(MIGRATIONS_DIR):
        os.makedirs(MIGRATIONS_DIR, exist_ok=True)
        return

    migration_files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
    if not migration_files:
        return

    print("Comprobando migraciones pendientes...")
    
    with get_db_connection() as conn:
        init_migrations_table(conn)
        applied = get_applied_migrations(conn)

        for filepath in migration_files:
            filename = os.path.basename(filepath)
            if filename not in applied:
                print(f"Aplicando migración: {filename}")
                try:
                    execute_sql_script(conn, filepath)
                    conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (filename,))
                    conn.commit()
                    print(f"Migración {filename} aplicada exitosamente.")
                except Exception as e:
                    conn.rollback()
                    print(f"Fallo al aplicar migración {filename}. Abortando. Error: {e}")
                    raise
