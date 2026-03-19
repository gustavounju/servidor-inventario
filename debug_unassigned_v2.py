from database.db_core import get_db_connection

def debug_unassigned():
    with get_db_connection() as conn:
        print("--- Tareas Sin PC Asignada (Unassigned in UI) ---")
        tasks = conn.execute("SELECT id, pc_name, descripcion, assigned_to, estado FROM tasks WHERE (pc_name IS NULL OR pc_name = '') AND estado != 'Hecha'").fetchall()
        for t in tasks:
            print(f"ID: {t['id']} | PC: '{t['pc_name']}' | Estado: {t['estado']} | Asignado: {t['assigned_to']} | Desc: {t['descripcion']}")
        print(f"Total: {len(tasks)}")

if __name__ == "__main__":
    debug_unassigned()
