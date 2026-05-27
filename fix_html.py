"""
Transforms pc_detail.html: replaces the vertical card cascade with Bootstrap tabs.
Tabs: Resumen | Tareas | Red & Energia | Componentes | Historial
"""

with open('templates/pc_detail.html', 'rb') as f:
    raw = f.read()

html = raw.decode('utf-8', errors='replace')

# Find the main container div opening and the closing </div><!-- /.container-fluid main -->
START_MARKER = '    <!-- BLOQUE 1: Datos principales de la PC -->'
END_MARKER = '  </div><!-- /.container-fluid main -->'

start_idx = html.find(START_MARKER)
end_idx = html.find(END_MARKER)

if start_idx == -1 or end_idx == -1:
    print(f"Markers not found: start={start_idx}, end={end_idx}")
    exit(1)

# Extract the existing blocks (we keep them, just wrap in tabs)
existing_bloque1 = html[start_idx : html.find('    <!-- BLOQUE 2:')]
existing_bloque2 = html[html.find('    <!-- BLOQUE 2:') : html.find('    {% if not pc.pc_name.upper().startswith(\'PC-GENERICA\') and not pc.pc_name.upper().startswith(\'PC GENERICA\') %}\n    <!-- BLOQUE 2.5:')]
existing_bloque25 = html[html.find('    {% if not pc.pc_name.upper().startswith(\'PC-GENERICA\') and not pc.pc_name.upper().startswith(\'PC GENERICA\') %}\n    <!-- BLOQUE 2.5:') : html.find('    {% if not pc.pc_name.upper().startswith(\'PC-GENERICA\') and not pc.pc_name.upper().startswith(\'PC GENERICA\') and not pc.pc_name.upper().startswith(\'INFRAESTRUCTURA\') %}\n    <!-- BLOQUE 2.8:')]
existing_bloque28 = html[html.find('    {% if not pc.pc_name.upper().startswith(\'PC-GENERICA\') and not pc.pc_name.upper().startswith(\'PC GENERICA\') and not pc.pc_name.upper().startswith(\'INFRAESTRUCTURA\') %}\n    <!-- BLOQUE 2.8:') : html.find('    <!-- BLOQUE 3:')]
existing_bloque3 = html[html.find('    <!-- BLOQUE 3:') : html.find('    <!-- BLOQUE 4:')]
existing_bloque4 = html[html.find('    <!-- BLOQUE 4:') : end_idx]

tabs_html = '''    <!-- NAV TABS -->
    <style>
      .pd-tabs { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 2px solid var(--border-color, #e2e8f0); }
      .pd-tab { padding: 8px 20px; border: none; background: none; color: var(--text-muted, #64748b); font-size: 0.87rem; font-weight: 600; cursor: pointer; border-radius: 6px 6px 0 0; transition: all 0.15s; }
      .pd-tab:hover { background: rgba(99,102,241,0.08); color: var(--accent-color, #6366f1); }
      .pd-tab.active { background: var(--accent-color, #6366f1); color: #fff; }
      .pd-tab-badge { background: rgba(255,255,255,0.3); color: inherit; border-radius: 10px; font-size: 0.7rem; padding: 1px 6px; margin-left: 5px; }
      .pd-pane { display: none; }
      .pd-pane.active { display: block; }
    </style>

    <div class="pd-tabs" id="pdTabBar">
      <button class="pd-tab active" onclick="switchTab('resumen', this)"><i class="bi bi-pc-display me-1"></i>Resumen</button>
      <button class="pd-tab" onclick="switchTab('tareas', this)"><i class="bi bi-list-task me-1"></i>Tareas <span class="pd-tab-badge">{{ tareas | length }}</span></button>
      <button class="pd-tab" onclick="switchTab('red', this)"><i class="bi bi-diagram-3 me-1"></i>Red y Energía</button>
      <button class="pd-tab" onclick="switchTab('componentes', this)"><i class="bi bi-cpu me-1"></i>Componentes</button>
      <button class="pd-tab" onclick="switchTab('historial', this)"><i class="bi bi-clock-history me-1"></i>Historial <span class="pd-tab-badge">{{ audit_logs | length }}</span></button>
    </div>

    <!-- TAB: RESUMEN -->
    <div class="pd-pane active" id="pane-resumen">
''' + existing_bloque1 + '''
    </div>

    <!-- TAB: TAREAS -->
    <div class="pd-pane" id="pane-tareas">
''' + existing_bloque3 + '''
    </div>

    <!-- TAB: RED Y ENERGÍA -->
    <div class="pd-pane" id="pane-red">
''' + existing_bloque2 + existing_bloque28 + '''
    </div>

    <!-- TAB: COMPONENTES -->
    <div class="pd-pane" id="pane-componentes">
''' + existing_bloque25 + '''
    </div>

    <!-- TAB: HISTORIAL -->
    <div class="pd-pane" id="pane-historial">
      <div class="d-flex justify-content-between align-items-center mb-2">
        <h5 class="mb-0" style="color:var(--text-color)"><i class="bi bi-clock-history me-1"></i>Historial de Cambios</h5>
        <button type="button" class="btn btn-sm btn-outline-dark" data-bs-toggle="modal" data-bs-target="#modalManualAudit">
          <i class="bi bi-pencil-square"></i> Registrar Cambio Manual
        </button>
      </div>
''' + existing_bloque4 + '''
    </div>

    <script>
    function switchTab(name, btn) {
      document.querySelectorAll('.pd-pane').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.pd-tab').forEach(b => b.classList.remove('active'));
      document.getElementById('pane-' + name).classList.add('active');
      btn.classList.add('active');
    }
    // Auto-activate tab based on hash
    (function(){
      var h = window.location.hash;
      if (h === '#tareas') switchTab('tareas', document.querySelectorAll('.pd-tab')[1]);
      else if (h === '#historial') switchTab('historial', document.querySelectorAll('.pd-tab')[4]);
    })();
    </script>
'''

new_html = html[:start_idx] + tabs_html + '\n  ' + html[end_idx:]

with open('templates/pc_detail.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Done. Tab structure applied.")
