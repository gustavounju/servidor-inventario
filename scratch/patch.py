import re

with open('templates/tecnicos.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Message Overlay
if 'id="messageOverlay"' not in content:
    content = content.replace('<!-- ── Auditoría de Racks ── -->', '''<!-- ── Mensaje / Comunicado Modal ── -->
<div class="voice-overlay" id="messageOverlay" onclick="closeMessageModal()">
  <div class="manual-sheet" onclick="event.stopPropagation()">
    <div class="sheet-handle"></div>
    <p style="font-size:1.1rem;font-weight:700;margin-bottom:12px;color:var(--text)" id="messageModalTitle"></p>
    <div class="input-group-gold" style="background: var(--bg-hover); padding: 12px; border-radius: 8px;">
      <p id="messageModalBody" style="margin:0; white-space: pre-wrap; font-size: 0.95rem; color: var(--text-muted); line-height: 1.5;"></p>
    </div>
    <div class="voice-actions" style="margin-top: 15px;">
      <button class="btn-vact btn-vsave" style="background: var(--primary); width: 100%;" onclick="closeMessageModal()">Entendido</button>
    </div>
  </div>
</div>

<!-- ── Auditoría de Racks ── -->''')

# 2. Add playMessageAlarm
if 'function playMessageAlarm()' not in content:
    content = content.replace('function playTaskAlarm() {', '''function playMessageAlarm() {
  try {
    if (navigator.vibrate) navigator.vibrate([100, 50, 100]);
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    const start = ctx.currentTime;
    [0, 0.2].forEach((offset) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, start + offset);
      gain.gain.setValueAtTime(0, start + offset);
      gain.gain.linearRampToValueAtTime(0.3, start + offset + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, start + offset + 0.15);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(start + offset);
      osc.stop(start + offset + 0.2);
    });
  } catch(e) {}
}

function playTaskAlarm() {''')

# 3. Replace alert with modal and add functions
if 'showMessageModal(' not in content:
    # replace aggressive playTaskAlarm with softer playMessageAlarm in poll()
    content = content.replace("alert(\"🔔 \" + msg.title + \"\\n\\n\" + msg.body);", "showMessageModal(msg.title, msg.body);")
    content = content.replace("playTaskAlarm();\\n      for (const msg of msgData.messages)", "playMessageAlarm();\\n      for (const msg of msgData.messages)")
    
    # insert the functions before init
    content = content.replace("// ── Init ──────────────────────────────────────────", """
// ── Modals / Comunicados ──────────────────────────
function showMessageModal(title, body) {
  const icon = title.includes('Administrador') ? '<i class="bi bi-megaphone-fill text-warning"></i> ' : '<i class="bi bi-bell-fill text-info"></i> ';
  document.getElementById('messageModalTitle').innerHTML = icon + title;
  document.getElementById('messageModalBody').textContent = body;
  document.getElementById('messageOverlay').classList.add('open');
}

function closeMessageModal() {
  document.getElementById('messageOverlay').classList.remove('open');
}

// ── Init ──────────────────────────────────────────
""")

with open('templates/tecnicos.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch applied to tecnicos.html")
