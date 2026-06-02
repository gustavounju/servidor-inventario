import re

# 1. Patch bp_tasks.py to include actions in API
with open('blueprints/bp_tasks.py', 'r', encoding='utf-8') as f:
    bp_tasks = f.read()

# Replace _attach_task_user_matches with _attach_task_actions_bulk(_attach_task_user_matches in api_visor_data
# We know api_visor_data() is around line 1000. Let's do string replacement.
old_rows_api = """                rows = _attach_task_user_matches(conn.execute(base_sql, params).fetchall(), conn)"""
new_rows_api = """                rows = _attach_task_actions_bulk(_attach_task_user_matches(conn.execute(base_sql, params).fetchall(), conn), conn)"""
bp_tasks = bp_tasks.replace(old_rows_api, new_rows_api)

old_hoy_api = """                tareas_hoy = _attach_task_user_matches(conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE DATE(t.created_at) = CURDATE() OR (t.estado = 'Hecha' AND DATE(t.completed_at) = CURDATE())
                    ORDER BY t.created_at DESC
                \"\"\").fetchall(), conn)"""
new_hoy_api = """                tareas_hoy = _attach_task_actions_bulk(_attach_task_user_matches(conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE DATE(t.created_at) = CURDATE() OR (t.estado = 'Hecha' AND DATE(t.completed_at) = CURDATE())
                    ORDER BY t.created_at DESC
                \"\"\").fetchall(), conn), conn)"""
bp_tasks = bp_tasks.replace(old_hoy_api, new_hoy_api)

old_ant_api = """                tareas_anteriores = _attach_task_user_matches(conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE DATE(t.created_at) < CURDATE() AND DATE(t.created_at) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    ORDER BY t.created_at DESC LIMIT 50
                \"\"\").fetchall(), conn)"""
new_ant_api = """                tareas_anteriores = _attach_task_actions_bulk(_attach_task_user_matches(conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE DATE(t.created_at) < CURDATE() AND DATE(t.created_at) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    ORDER BY t.created_at DESC LIMIT 50
                \"\"\").fetchall(), conn), conn)"""
bp_tasks = bp_tasks.replace(old_ant_api, new_ant_api)

old_pend_api = """                tareas_pendientes = _attach_task_user_matches(conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE t.estado != 'Hecha'
                    ORDER BY t.created_at DESC
                \"\"\").fetchall(), conn)"""
new_pend_api = """                tareas_pendientes = _attach_task_actions_bulk(_attach_task_user_matches(conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE t.estado != 'Hecha'
                    ORDER BY t.created_at DESC
                \"\"\").fetchall(), conn), conn)"""
bp_tasks = bp_tasks.replace(old_pend_api, new_pend_api)

with open('blueprints/bp_tasks.py', 'w', encoding='utf-8') as f:
    f.write(bp_tasks)

# 2. Patch visor_tareas.html JS
with open('templates/visor_tareas.html', 'r', encoding='utf-8') as f:
    visor = f.read()

acciones_js = """
                        ${task.acciones && task.acciones.length > 0 ? `
                        <div class="mt-2" style="background: rgba(14, 165, 233, 0.05); border-left: 2px solid #0ea5e9; padding: 6px; border-radius: 4px;">
                            ${task.acciones.map(accion => `
                            <div class="small" style="color: #64748b; margin-bottom: 2px;">
                                <i class="bi bi-chat-text me-1"></i>
                                <strong style="color: #334155;">${accion.technician_name}:</strong> ${accion.action_text}
                            </div>
                            `).join('')}
                        </div>
                        ` : ''}
"""

# The JS templates look like:
# <div>${task.descripcion}</div>
# ${task.solucion ? `<div ...>...</div>` : ''}
visor = re.sub(r'(<div>\$\{task\.descripcion\}</div>)', r'\1' + acciones_js, visor)
visor = re.sub(r'(<div class="fw-medium" style="[^"]*" title="\$\{task\.descripcion\}">\$\{task\.descripcion\}</div>)', r'\1' + acciones_js, visor)

with open('templates/visor_tareas.html', 'w', encoding='utf-8') as f:
    f.write(visor)

print("JS rendering updated")
