with open('templates/_shared_modals.html', 'rb') as f:
    content = f.read().decode('utf-8')

old_str = "openCompleteTaskModal('{{ t.id }}', '{{ t.assigned_to or '' }}')"
new_str = "openCompleteTaskModal('{{ t.id }}', '{{ t.assigned_to or '' }}', '{{ pc.pc_name }}')"
content = content.replace(old_str, new_str)

with open('templates/_shared_modals.html', 'wb') as f:
    f.write(content.encode('utf-8'))
print("Done _shared_modals")
