import re

with open('templates/_shared_modals.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the badge
content = content.replace('${renderTaskMatchBox(t)}', '')

old_actions = """                <div class="pt-actions">
                    <button class="btn-pt-action btn-pt-confirm" onclick='quickTaskDone(${t.id}, ${JSON.stringify(pcName)}, ${JSON.stringify(t.assigned_to || "")})'>
                        <i class="bi bi-check-lg"></i> Confirmar
                    </button>"""

new_actions = """                <div class="pt-actions">
                    <button class="btn-pt-action btn-pt-confirm" onclick='quickTaskDone(${t.id}, ${JSON.stringify(pcName)}, ${JSON.stringify(t.assigned_to || "")})'>
                        <i class="bi bi-check-lg"></i> Confirmar
                    </button>
                    <button class="btn-pt-action" style="border-color:#bae6fd; background:#e0f2fe; color:#0284c7; flex:0 0 38px;" onclick="openTaskActionsModal(${t.id})" title="Acciones">
                        <i class="bi bi-card-list"></i>
                    </button>"""

if old_actions in content:
    content = content.replace(old_actions, new_actions)
    print("Replaced actions")
else:
    print("Could not find actions to replace")

with open('templates/_shared_modals.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched _shared_modals.html successfully')
