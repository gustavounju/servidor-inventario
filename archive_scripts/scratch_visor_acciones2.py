
with open('blueprints/bp_tasks.py', 'r', encoding='utf-8') as f:
    bp_tasks = f.read()

helper = """
def _attach_task_actions_bulk(tasks, conn):
    if not tasks:
        return tasks
    task_ids = [t['id'] for t in tasks]
    placeholders = ', '.join(['%s'] * len(task_ids))
    actions = conn.execute(f"SELECT * FROM task_actions WHERE task_id IN ({placeholders}) ORDER BY created_at ASC", tuple(task_ids)).fetchall()
    
    from collections import defaultdict
    actions_map = defaultdict(list)
    for a in actions:
        actions_map[a['task_id']].append(a)
        
    for t in tasks:
        t['acciones'] = actions_map.get(t['id'], [])
    return tasks

"""

if '_attach_task_actions_bulk' not in bp_tasks:
    bp_tasks = bp_tasks.replace('@bp_tasks.route("/visor")', helper + '@bp_tasks.route("/visor")')

# Replace in def visor() specifically
old_visor = """                tareas = _attach_task_user_matches(conn.execute(base_sql, params).fetchall(), conn)"""
new_visor = """                tareas = _attach_task_actions_bulk(_attach_task_user_matches(conn.execute(base_sql, params).fetchall(), conn), conn)"""
bp_tasks = bp_tasks.replace(old_visor, new_visor)

old_hoy = """                tareas_hoy = _attach_task_user_matches(conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE DATE(t.created_at) = CURDATE() OR (t.estado = 'Hecha' AND DATE(t.completed_at) = CURDATE())
                    ORDER BY t.created_at DESC
                \"\"\").fetchall(), conn)"""
new_hoy = """                tareas_hoy = _attach_task_actions_bulk(_attach_task_user_matches(conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE DATE(t.created_at) = CURDATE() OR (t.estado = 'Hecha' AND DATE(t.completed_at) = CURDATE())
                    ORDER BY t.created_at DESC
                \"\"\").fetchall(), conn), conn)"""
bp_tasks = bp_tasks.replace(old_hoy, new_hoy)

old_ant = """                tareas_anteriores = _attach_task_user_matches(conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE DATE(t.created_at) < CURDATE() AND DATE(t.created_at) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    ORDER BY t.created_at DESC LIMIT 50
                \"\"\").fetchall(), conn)"""
new_ant = """                tareas_anteriores = _attach_task_actions_bulk(_attach_task_user_matches(conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE DATE(t.created_at) < CURDATE() AND DATE(t.created_at) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    ORDER BY t.created_at DESC LIMIT 50
                \"\"\").fetchall(), conn), conn)"""
bp_tasks = bp_tasks.replace(old_ant, new_ant)

old_pend = """                tareas_pendientes = _attach_task_user_matches(conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE t.estado != 'Hecha'
                    ORDER BY t.created_at DESC
                \"\"\").fetchall(), conn)"""
new_pend = """                tareas_pendientes = _attach_task_actions_bulk(_attach_task_user_matches(conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE t.estado != 'Hecha'
                    ORDER BY t.created_at DESC
                \"\"\").fetchall(), conn), conn)"""
bp_tasks = bp_tasks.replace(old_pend, new_pend)

with open('blueprints/bp_tasks.py', 'w', encoding='utf-8') as f:
    f.write(bp_tasks)

print("bp_tasks.py patched correctly")
