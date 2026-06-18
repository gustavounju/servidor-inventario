import re
with open('templates/pc_detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r"(<i class=\"bi bi-check-lg\"></i> Hecha\s*</button>\s*{%\s*endif\s*%})")
replacement = r"\1\n              <button type=\"button\" class=\"btn btn-sm mb-1\" style=\"background-color: #0ea5e9; color: white; border: none;\" onclick=\"openTaskActionsModal('{{ t.id }}')\">\n                <i class=\"bi bi-card-list\"></i> Acciones\n              </button>"

new_content = pattern.sub(replacement, content)
with open('templates/pc_detail.html', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("pc_detail.html updated")

with open('templates/visor_tareas.html', 'r', encoding='utf-8') as f:
    content2 = f.read()

pattern2 = re.compile(r"(<i class=\"bi bi-check-lg\"></i> Hecha\s*</button>\s*`;\s*})")
replacement2 = r"\1\n            actionButtons += `\n                <button class=\"btn btn-sm mb-1 w-100\" style=\"background-color: #0ea5e9; color: white; border: none;\" onclick=\"openTaskActionsModal('${task.id}')\">\n                    <i class=\"bi bi-card-list\"></i> Acciones\n                </button>\n            `;"

new_content2 = pattern2.sub(replacement2, content2)
with open('templates/visor_tareas.html', 'w', encoding='utf-8') as f:
    f.write(new_content2)
print("visor_tareas.html updated")

