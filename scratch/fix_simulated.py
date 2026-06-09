import sqlite3
conn = sqlite3.connect('inventario.db')
conn.execute("UPDATE tasks SET pc_name = '' WHERE descripcion LIKE 'Prueba de coincidencia%'")
conn.commit()
count = conn.execute("SELECT COUNT(*) FROM tasks WHERE pc_name = '' AND descripcion LIKE 'Prueba de coincidencia%'").fetchone()[0]
print(f"{count} tareas actualizadas a huérfanas")
