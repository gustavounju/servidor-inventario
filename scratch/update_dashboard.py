import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add the inline AD matches to the Description column
new_desc_cell = """<td>
                                {{ task.descripcion }}
                                {% if task.has_user_match %}
                                <div class="mt-2 p-2 rounded" style="background: rgba(34, 197, 94, 0.05); border: 1px solid rgba(34, 197, 94, 0.2);">
                                    <div class="small fw-bold text-success mb-1" style="font-size: 0.7rem; text-transform: uppercase;"><i class="bi bi-robot me-1"></i> Resolución Inteligente ({% if task.matched_pc_count == 1 %}1 coincidencia{% else %}{{ task.matched_pc_count }} coincidencias{% endif %})</div>
                                    <div class="d-flex flex-wrap gap-1">
                                        {% for pc_match in task.matched_pcs %}
                                        <button class="btn btn-sm btn-outline-success py-0 px-2" style="font-size: 0.75rem; border-radius: 4px;" onclick="quickAssignDashboard('{{ task.id }}', '{{ pc_match.pc_name }}')" title="Asignar rápidamente a esta PC">
                                            {{ pc_match.pc_name }}{% if pc_match.fuero %} <span class="opacity-75">· {{ pc_match.fuero }}</span>{% endif %}
                                        </button>
                                        {% endfor %}
                                    </div>
                                </div>
                                {% endif %}
                            </td>"""

content = re.sub(r'<td>\{\{\s*task\.descripcion\s*\}\}</td>', new_desc_cell, content)

# Add quickAssignDashboard function
js_function = """// INLINE ASSIGN LOGIC (No Modals)
        async function quickAssignDashboard(taskId, pcName) {
            if (!confirm(`¿Confirmar asignación automática a la PC ${pcName}?`)) return;
            const fd = new FormData();
            fd.append('task_id', taskId);
            fd.append('pc_name', pcName);
            
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            if (csrfToken) {
                fd.append('csrf_token', csrfToken);
            }
            
            try {
                const r = await fetch('/tasks/assign', { method: 'POST', body: fd });
                if (r.ok) window.location.reload();
            } catch (e) { console.error(e); }
        }

        function toggleAssignForm(taskId) {"""

content = re.sub(r'// INLINE ASSIGN LOGIC \(No Modals\)\n\s*function toggleAssignForm\(taskId\) \{', js_function, content)


with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Dashboard actualizado con éxito.")
