from database.db_core import get_db_connection
import random

with get_db_connection() as conn:
    pcs = conn.execute('SELECT pc_name, last_user, fuero FROM pcs').fetchall()
    pcs_list = [{'pc_name': p['pc_name'], 'last_user': p['last_user'], 'fuero': p['fuero']} for p in pcs]

    while len(pcs_list) < 5:
        dummy_name = f'PC-DUMMY-{random.randint(100, 999)}'
        dummy_user = f'Usuario {random.randint(1, 100)}'
        conn.execute('INSERT IGNORE INTO pcs (pc_name, last_user, fuero, is_active) VALUES (%s, %s, %s, %s)', (dummy_name, dummy_user, 'Civil', 'True'))
        pcs_list.append({'pc_name': dummy_name, 'last_user': dummy_user, 'fuero': 'Civil'})

    # Delete previous tasks if any to keep clean
    conn.execute("DELETE FROM tasks WHERE descripcion LIKE 'Prueba de coincidencia%'")

    for p in pcs_list[:5]:
        pc_name = p['pc_name']
        user = p['last_user'] if p['last_user'] else f'User_of_{pc_name}'
        fuero = p['fuero'] if p['fuero'] else 'Penal'
        
        desc = f'Prueba de coincidencia para {pc_name} y usuario {user}'
        
        conn.execute('INSERT INTO tasks (pc_name, solicitante, descripcion, estado, fuero, tipo_actividad) VALUES (%s, %s, %s, %s, %s, %s)',
                       (None, user, desc, 'Pendiente', fuero, 'tarea'))

    conn.commit()
    count = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE pc_name IS NULL AND descripcion LIKE 'Prueba de coincidencia%'").fetchone()['c']
    print(f"Se insertaron {count} tareas de prueba huérfanas en MySQL.")
