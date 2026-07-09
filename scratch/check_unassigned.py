from database.db_core import get_db_connection

def check_tasks():
    with get_db_connection() as conn:
        print("--- Tareas No Asignadas ---")
        tasks = conn.execute("SELECT id, descripcion, assigned_to, estado FROM tasks WHERE assigned_to IS NULL OR assigned_to = ''").fetchall()
        for t in tasks:
            print(f"ID: {t['id']} | Estado: {t['estado']} | Desc: {t['descripcion'][:30]}...")
        print(f"Total: {len(tasks)}")

if __name__ == "__main__":
    check_tasks()
