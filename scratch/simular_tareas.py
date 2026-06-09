import sqlite3
import random

conn = sqlite3.connect('inventario.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

pcs = cursor.execute('SELECT pc_name, last_user, fuero FROM pcs').fetchall()
pcs_list = [{'pc_name': p['pc_name'], 'last_user': p['last_user'], 'fuero': p['fuero']} for p in pcs]

while len(pcs_list) < 5:
    dummy_name = f'PC-DUMMY-{random.randint(100, 999)}'
    dummy_user = f'Usuario {random.randint(1, 100)}'
    cursor.execute('INSERT INTO pcs (pc_name, last_user, fuero, is_active) VALUES (?, ?, ?, ?)', (dummy_name, dummy_user, 'Civil', 'True'))
    pcs_list.append({'pc_name': dummy_name, 'last_user': dummy_user, 'fuero': 'Civil'})

# Create exactly 5 tasks for the first 5 pcs
for p in pcs_list[:5]:
    pc_name = p['pc_name']
    user = p['last_user'] if p['last_user'] else f'User_of_{pc_name}'
    fuero = p['fuero'] if p['fuero'] else 'Penal'
    
    desc = f'Prueba de coincidencia para {pc_name} y usuario {user}'
    
    cursor.execute('INSERT INTO tasks (pc_name, solicitante, descripcion, estado, fuero) VALUES (?, ?, ?, ?, ?)',
                   (pc_name, user, desc, 'Pendiente', fuero))

conn.commit()
print("Se insertaron 5 tareas de prueba.")
