from database.migrations import run_all_migrations
from database.db_core import init_db

if __name__ == "__main__":
    print("Iniciando ejecución de migraciones...")
    init_db()
    run_all_migrations()
    print("Ejecución finalizada.")
