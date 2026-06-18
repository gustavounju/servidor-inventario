import re

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

    bp_tasks = bp_tasks.replace(
        'tareas = _attach_task_user_matches(',
        'tareas = _attach_task_actions_bulk(_attach_task_user_matches('
    )
    bp_tasks = bp_tasks.replace(
        'tareas_hoy = _attach_task_user_matches(',
        'tareas_hoy = _attach_task_actions_bulk(_attach_task_user_matches('
    )
    bp_tasks = bp_tasks.replace(
        'tareas_anteriores = _attach_task_user_matches(',
        'tareas_anteriores = _attach_task_actions_bulk(_attach_task_user_matches('
    )
    bp_tasks = bp_tasks.replace(
        'tareas_pendientes = _attach_task_user_matches(',
        'tareas_pendientes = _attach_task_actions_bulk(_attach_task_user_matches('
    )

    # We need to fix the closing parenthesis for the nested calls
    # For `tareas = _attach_task_actions_bulk(_attach_task_user_matches(conn.execute(base_sql, params).fetchall(), conn)` we need an extra `), conn)`
    # Since we replaced the prefix, we just need to replace `fetchall(), conn)` with `fetchall(), conn), conn)` ONLY inside def visor().
    
    # Better approach: string replacement for the exact lines
    lines = bp_tasks.split('\\n')
    in_visor = False
    for i, line in enumerate(lines):
        if 'def visor():' in line:
            in_visor = True
        if in_visor and 'fetchall(), conn)' in line and '_attach_task_actions_bulk' in line:
            lines[i] = line.replace('fetchall(), conn)', 'fetchall(), conn), conn)')
        if in_visor and 'return render_template' in line:
            in_visor = False # roughly end of DB queries

    with open('blueprints/bp_tasks.py', 'w', encoding='utf-8') as f:
        f.write('\\n'.join(lines))
    print("bp_tasks.py patched")


with open('templates/visor_tareas.html', 'r', encoding='utf-8') as f:
    visor = f.read()

acciones_html = """
                                {% if task.acciones %}
                                <div class="mt-2" style="background: rgba(14, 165, 233, 0.05); border-left: 2px solid #0ea5e9; padding: 6px; border-radius: 4px;">
                                    {% for accion in task.acciones %}
                                    <div class="small" style="color: #64748b; margin-bottom: 2px;">
                                        <i class="bi bi-chat-text me-1"></i>
                                        <strong style="color: #334155;">{{ accion.technician_name }}:</strong> {{ accion.action_text }}
                                    </div>
                                    {% endfor %}
                                </div>
                                {% endif %}
"""

# There are multiple <td class="desc-cell"> blocks
# Let's just do a regex replace to insert after `<div>{{ task.descripcion }}</div>`
# Wait, some blocks have `{% if task.solucion %}`
# So let's insert it right before `</td>` in `<td class="desc-cell">`
# Better to do it after task.descripcion directly, or task.solucion if it exists.
# `visor_tareas.html` has 3 tables: pendientes, hoy, historial.
# Let's replace `</td>` inside those specific blocks, or simpler: find `<div>{{ task.descripcion }}</div>`

# We will replace `<div>{{ task.descripcion }}</div>` with `<div>{{ task.descripcion }}</div>` + acciones_html (so it applies to all tables)
# Wait, in some it's `<div class="fw-medium" style="color: #1e293b; ..." title="{{ t.descripcion }}">{{ t.descripcion }}</div>`
# Let's look at the exact HTML.

visor = re.sub(r'(<div>\{\{ task\.descripcion \}\}</div>)', r'\\1' + acciones_html, visor)
visor = re.sub(r'(<div class="fw-medium" style="[^"]*" title="\{\{ task\.descripcion \}\}">\{\{ task\.descripcion \}\}</div>)', r'\\1' + acciones_html, visor)

with open('templates/visor_tareas.html', 'w', encoding='utf-8') as f:
    f.write(visor)
print("visor_tareas.html patched")
