
with open('templates/tecnicos.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Insert HTML overlay
html_to_insert = """<!-- ── Historial de Acciones ── -->
<div class="voice-overlay" id="taskActionsOverlay">
  <div class="manual-sheet" style="max-height: 85vh; overflow-y: auto;">
    <div class="sheet-handle"></div>
    <p style="font-size:.94rem;font-weight:700;margin-bottom:6px;"><i class="bi bi-card-list" style="color:#0ea5e9"></i> Registro de Acciones</p>
    
    <div id="mobileTaskActionsList" style="margin-bottom: 15px; font-size: 0.85rem; max-height: 40vh; overflow-y: auto; background: var(--bg3); border-radius: 8px; padding: 10px;">
        <div class="text-center text-muted py-2"><div class="spinner-border spinner-border-sm"></div> Cargando...</div>
    </div>

    <div class="input-group-gold">
      <div class="input-label-gold">Agregar Acción</div>
      <textarea class="gold-input" id="mobileNewTaskAction" rows="3" placeholder="Describe la acción (ej. Llevé la PC al taller)"></textarea>
    </div>

    <input type="hidden" id="mobileActionTaskId">

    <div class="voice-actions">
      <button class="btn-vact btn-vcancel" onclick="closeTaskActionsOverlay()">Cerrar</button>
      <button class="btn-vact btn-vsave" style="background: #0ea5e9;" onclick="submitMobileTaskAction()"><i class="bi bi-save"></i> Guardar Acción</button>
    </div>
  </div>
</div>

"""

if 'taskActionsOverlay' not in content:
    content = content.replace('<!-- ── Completar / Editar Tarea ── -->', html_to_insert + '<!-- ── Completar / Editar Tarea ── -->')

# 2. Modify taskCard actions
old_actions = """  const actions = mode === 'free'
    ? `<button class="btn-act btn-claim" onclick="claimTask(${t.id})"><i class="bi bi-hand-index-thumb"></i> Tomar</button>`
    : mode === 'mine'
    ? `<button class="btn-act btn-claim" style="background:var(--bg3); color:var(--text);" onclick="editTask(${t.id})"><i class="bi bi-pencil"></i> Editar</button>
       <button class="btn-act btn-done" onclick="openCompleteModal(${t.id})"><i class="bi bi-check-lg"></i> Completar</button>`
    : '';"""

new_actions = """  const actions = mode === 'free'
    ? `<button class="btn-act btn-claim" onclick="claimTask(${t.id})"><i class="bi bi-hand-index-thumb"></i> Tomar</button>`
    : mode === 'mine'
    ? `<button class="btn-act btn-claim" style="background:var(--bg3); color:var(--text);" onclick="editTask(${t.id})"><i class="bi bi-pencil"></i> Editar</button>
       <button class="btn-act btn-done" onclick="openCompleteModal(${t.id})"><i class="bi bi-check-lg"></i> Completar</button>
       <button class="btn-act w-100" style="background:#0ea5e9; color:white; margin-top:5px;" onclick="openTaskActionsOverlay(${t.id})"><i class="bi bi-card-list"></i> Acciones</button>`
    : '';"""

content = content.replace(old_actions, new_actions)

# 3. Insert JS
js_to_insert = """
function openTaskActionsOverlay(taskId) {
    document.getElementById('mobileActionTaskId').value = taskId;
    document.getElementById('mobileNewTaskAction').value = '';
    document.getElementById('taskActionsOverlay').classList.add('open');
    loadMobileTaskActions(taskId);
}

function closeTaskActionsOverlay() {
    document.getElementById('taskActionsOverlay').classList.remove('open');
}

function loadMobileTaskActions(taskId) {
    const list = document.getElementById('mobileTaskActionsList');
    list.innerHTML = '<div class="text-center text-muted py-2">Cargando...</div>';
    fetch(`/api/tasks/${taskId}/actions`)
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') {
                if(data.actions.length === 0) {
                    list.innerHTML = '<div class="text-center text-muted py-2">Sin acciones registradas.</div>';
                } else {
                    list.innerHTML = data.actions.map(a => `
                        <div style="background: var(--bg); border: 1px solid rgba(0,0,0,0.05); border-radius: 6px; padding: 8px; margin-bottom: 6px;">
                            <div style="display:flex; justify-content:space-between; margin-bottom:4px; font-size:0.75rem;">
                                <strong>${a.user_name}</strong>
                                <span style="color:var(--text-muted)">${a.created_at_fmt}</span>
                            </div>
                            <div style="white-space:pre-wrap;">${a.action_text}</div>
                        </div>
                    `).join('');
                }
            } else {
                list.innerHTML = '<div class="text-danger py-2">Error al cargar.</div>';
            }
        })
        .catch(err => list.innerHTML = '<div class="text-danger py-2">Error de conexión.</div>');
}

function submitMobileTaskAction() {
    const taskId = document.getElementById('mobileActionTaskId').value;
    const text = document.getElementById('mobileNewTaskAction').value.trim();
    if (!text) return alert("El texto no puede estar vacío.");
    
    const formData = new FormData();
    formData.append('action_text', text);
    formData.append('csrf_token', CSRF);
    
    fetch(`/api/tasks/${taskId}/actions`, {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('mobileNewTaskAction').value = '';
            loadMobileTaskActions(taskId);
        } else {
            alert(data.message || 'Error al guardar.');
        }
    })
    .catch(err => alert("Error de conexión."));
}
</script>"""

if 'function openTaskActionsOverlay' not in content:
    content = content.replace('</script>', js_to_insert, 1) # Only replace the first match or the specific one at the end

with open('templates/tecnicos.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('tecnicos.html patched successfully')
