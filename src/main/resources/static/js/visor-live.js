(() => {
    'use strict';
    const toggle = document.getElementById('visor-live');
    const status = document.getElementById('visor-live-status');
    let edited = false;
    document.addEventListener('input', event => {
        if (event.target.closest('form') && event.target !== toggle) {
            edited = true;
            status.textContent = 'Pausado: cambios sin guardar';
        }
    });
    async function update() {
        try {
            if (!toggle.checked || edited || document.activeElement?.closest('form')) return;
            const response = await fetch(location.href, { credentials: 'same-origin', cache: 'no-store', signal: AbortSignal.timeout(15000) });
            if (response.redirected || response.status === 401 || response.status === 403) {
                toggle.checked = false;
                status.textContent = 'Vuelva a ingresar';
                return;
            }
            if (!response.ok) throw new Error('Conexion');
            const next = new DOMParser().parseFromString(await response.text(), 'text/html');
            // El usuario pudo empezar a escribir mientras viajaba la respuesta; comprobar otra vez antes de reemplazar.
            if (edited || !toggle.checked || document.activeElement?.closest('form')) return;
            for (const selector of ['.task-metric-grid', '.task-board']) {
                const current = document.querySelector(selector), fresh = next.querySelector(selector);
                if (current && fresh) current.replaceWith(fresh);
            }
            status.textContent = 'Actualizado ' + new Date().toLocaleTimeString('es-AR');
        } catch {
            status.textContent = 'Sin conexion. Reintentando...';
        } finally { setTimeout(update, 30000); }
    }
    setTimeout(update, 30000);
})();
