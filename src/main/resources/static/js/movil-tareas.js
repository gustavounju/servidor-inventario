(() => {
    'use strict';
    const $ = id => document.getElementById(id);
    const base = document.body.dataset.base;
    const api = 'api/v1/tareas-tecnicas';
    const csrf = document.querySelector('meta[name="csrf-token"]').content;
    const csrfHeader = document.querySelector('meta[name="csrf-header"]').content;
    const native = navigator.userAgent.includes('InventarioLAN/');
    let session, tasks = [], selected, editing, filter = 'pending', limit = 40;
    let cursor, cursorKey, busy = false, audio, sound = false, stopped = false;
    // Los previews de comentarios se cargan aparte para no retrasar el listado principal de tareas.
    let renderToken = 0, domainTimer;
    const commentPreviewCache = new Map(), domainUsers = new Map();
    const icons = () => window.lucide?.createIcons();
    const isOpen = task => ['PENDIENTE', 'EN_PROCESO'].includes(task.estado);
    const owns = task => task.responsable?.toLowerCase() === session.usuario.username.toLowerCase();
    const mayEdit = task => session.puedeEditar && (session.administrador || owns(task));
    const status = task => isOpen(task) ? 'Pendiente' : task.estado === 'CERRADA' ? 'Finalizada' : 'Cancelada';
    const date = value => value ? new Date(value).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' }) : '-';
    function message(text, error = false, target = 'message') {
        $(target).textContent = text;
        $(target).classList.toggle('error', error);
        $(target).hidden = !text;
    }
    function element(tag, text, className) {
        const node = document.createElement(tag);
        if (text != null) node.textContent = text;
        if (className) node.className = className;
        return node;
    }
    async function request(path, method = 'GET', data) {
        const response = await fetch(base + path, {
            method, credentials: 'same-origin', cache: 'no-store',
            headers: { Accept: 'application/json', ...(method !== 'GET' ? { [csrfHeader]: csrf, 'Content-Type': 'application/json' } : {}) },
            ...(data !== undefined ? { body: JSON.stringify(data) } : {}), signal: AbortSignal.timeout(15000)
        });
        if (response.status === 401 || response.redirected) {
            stopped = true;
            location.assign(base + 'movil/login');
            throw new Error('La sesion vencio. Ingrese nuevamente.');
        }
        if (!response.ok) {
            const errors = { 403: 'No tiene permiso para esta operacion o la sesion cambio. Vuelva a ingresar.',
                404: 'La tarea ya no existe.', 409: 'La tarea ya fue tomada o esta finalizada. Actualice la lista.',
                400: 'Revise los campos obligatorios y su longitud.' };
            throw new Error(errors[response.status] || 'No se pudo guardar. Intente nuevamente.');
        }
        return response.status === 204 ? null : response.json();
    }
    function render() {
        const token = ++renderToken;
        const today = new Date().toLocaleDateString('en-CA');
        $('pending-count').textContent = tasks.filter(isOpen).length;
        $('mine-count').textContent = tasks.filter(t => isOpen(t) && owns(t)).length;
        $('done-count').textContent = tasks.filter(t => t.estado === 'CERRADA' && t.cerradoEn && new Date(t.cerradoEn).toLocaleDateString('en-CA') === today).length;
        const query = $('search').value.trim().toLocaleLowerCase();
        const found = tasks.filter(t => {
            const match = filter === 'all' || (filter === 'pending' && isOpen(t)) || (filter === 'mine' && owns(t)) || (filter === 'done' && !isOpen(t));
            const text = [t.id, t.titulo, t.descripcion, t.equipoNombre, t.solicitanteUsername, t.solicitanteNombre, t.solicitanteFuero, t.responsable].join(' ').toLocaleLowerCase();
            return match && text.includes(query);
        });
        $('task-list').replaceChildren();
        for (const t of found.slice(0, limit)) {
            const row = element('article', null, 'task-row');
            const title = element('button', '#' + t.id + '  ' + t.titulo, 'task-open');
            title.onclick = () => openDetail(t);
            const badge = element('span', status(t), 'badge' + (t.estado === 'CERRADA' ? ' done' : t.estado === 'CANCELADA' ? ' cancelled' : ''));
            row.append(title, badge);
            if (t.descripcion) row.append(element('p', t.descripcion, 'task-description'));
            const meta = element('div', null, 'task-meta');
            meta.append(element('span', t.responsable || 'Sin tomar'), element('span', t.solicitanteFuero || '-'),
                element('span', t.prioridad, ['ALTA', 'URGENTE'].includes(t.prioridad) ? 'priority-high' : ''), element('span', date(t.creadoEn)));
            row.append(meta);
            const preview = element('section', 'Cargando comentarios...', 'task-comments-preview muted');
            preview.id = 'comments-preview-' + t.id;
            preview.setAttribute('aria-label', 'Comentarios de la tarea ' + t.id);
            row.append(preview);
            $('task-list').append(row);
            loadCommentPreview(t.id, token);
        }
        $('result-count').textContent = found.length + ' tareas';
        $('empty').hidden = found.length !== 0;
        $('more').hidden = found.length <= limit;
        $('task-list').setAttribute('aria-busy', 'false');
    }
    async function refresh() {
        tasks = await request(api);
        render();
    }
    async function comments(id) {
        const list = await request(api + '/' + id + '/comentarios');
        commentPreviewCache.set(id, list);
        if (selected?.id !== id) return;
        $('comments').replaceChildren();
        if (!list.length) $('comments').append(element('p', 'Sin comentarios.', 'muted'));
        for (const c of list) {
            const item = element('article', null, 'comment');
            item.append(element('small', c.autor + ' | ' + date(c.creadoEn)), element('p', c.comentario));
            $('comments').append(item);
        }
    }
    function renderCommentPreview(id, list) {
        const preview = $('comments-preview-' + id);
        if (!preview) return;
        preview.replaceChildren();
        if (!list.length) {
            preview.textContent = 'Sin comentarios cargados.';
            return;
        }
        preview.classList.remove('muted');
        preview.append(element('strong', 'Comentarios'));
        for (const c of list.slice(0, 2)) {
            preview.append(element('span', c.autor + ': ' + c.comentario));
        }
    }
    async function loadCommentPreview(id, token) {
        if (commentPreviewCache.has(id)) {
            renderCommentPreview(id, commentPreviewCache.get(id));
            return;
        }
        try {
            const list = await request(api + '/' + id + '/comentarios');
            commentPreviewCache.set(id, list);
            if (token === renderToken) renderCommentPreview(id, list);
        } catch {
            const preview = $('comments-preview-' + id);
            if (preview && token === renderToken) preview.textContent = 'No se pudieron cargar comentarios.';
        }
    }
    async function openDetail(task) {
        selected = task;
        $('detail-title').textContent = '#' + task.id + '  ' + task.titulo;
        $('detail-status').textContent = status(task) + ' | Prioridad ' + task.prioridad;
        $('detail-description').textContent = task.descripcion || 'Sin descripcion.';
        $('detail-meta').replaceChildren();
        for (const [key, value] of Object.entries({ Solicitante: task.solicitanteNombre, Usuario: task.solicitanteUsername, Oficina: task.solicitanteFuero,
            Responsable: task.responsable || 'Sin tomar', Equipo: task.equipoNombre, Creada: date(task.creadoEn), Finalizada: date(task.cerradoEn) })) {
            $('detail-meta').append(element('dt', key), element('dd', value || '-'));
        }
        $('take-task').hidden = !session.puedeEditar || !!task.responsable || !isOpen(task);
        for (const id of ['edit-task', 'delete-task', 'state-form', 'comment-form']) $(id).hidden = !mayEdit(task);
        $('state-form').elements.estado.value = isOpen(task) ? 'PENDIENTE' : task.estado;
        $('state-form').elements.observacionesCierre.value = task.observacionesCierre || '';
        $('comment-form').reset();
        message('', false, 'detail-message');
        $('comments').textContent = 'Cargando comentarios...';
        if (!$('detail-dialog').open) $('detail-dialog').showModal();
        try { await comments(task.id); } catch (error) { message(error.message, true, 'detail-message'); }
    }
    async function act(action, target = 'detail-message') {
        if (busy) return;
        busy = true;
        document.querySelectorAll('dialog button').forEach(button => button.disabled = true);
        try { await action(); } catch (error) { message(error.message || 'Sin conexion con el servidor.', true, target); }
        finally {
            busy = false;
            document.querySelectorAll('dialog button').forEach(button => button.disabled = false);
        }
    }
    function openForm(task = null) {
        editing = task;
        const form = $('task-form');
        form.reset();
        $('form-title').textContent = task ? 'Editar tarea #' + task.id : 'Nueva tarea';
        const defaults = task || { solicitanteUsername: session.usuario.username, solicitanteNombre: session.usuario.nombreVisible, solicitanteFuero: session.usuario.fuero, prioridad: 'MEDIA' };
        for (const control of form.elements) if (control.name && defaults[control.name] != null) control.value = defaults[control.name];
        $('responsable-field').hidden = !session.administrador;
        $('solicitante-help').textContent = 'Escriba al menos 2 caracteres para buscar en AD.';
        message('', false, 'form-message');
        $('task-dialog').showModal();
    }
    $('task-form').onsubmit = event => {
        event.preventDefault();
        act(async () => {
            const data = Object.fromEntries(new FormData(event.target));
            data.equipoId = editing?.equipoId || null;
            data.responsable = data.responsable?.trim() || null;
            const saved = await request(api + (editing ? '/' + editing.id : ''), editing ? 'PUT' : 'POST', data);
            $('task-dialog').close();
            commentPreviewCache.delete(saved.id);
            await refresh();
            await openDetail(tasks.find(t => t.id === saved.id) || saved);
            message('Tarea guardada.', false, 'detail-message');
        }, 'form-message');
    };
    $('take-task').onclick = () => act(async () => {
        const task = await request(api + '/' + selected.id + '/tomar', 'POST');
        await refresh(); await openDetail(task); message('La tarea quedo a su cargo.', false, 'detail-message');
    });
    $('state-form').onsubmit = event => {
        event.preventDefault();
        act(async () => {
            const data = Object.fromEntries(new FormData(event.target));
            if (selected.estado === 'EN_PROCESO' && data.estado === 'PENDIENTE') data.estado = 'EN_PROCESO';
            const task = await request(api + '/' + selected.id + '/estado', 'PATCH', data);
            await refresh(); await openDetail(task); message('Estado guardado.', false, 'detail-message');
        });
    };
    $('comment-form').onsubmit = event => {
        event.preventDefault();
        act(async () => {
            await request(api + '/' + selected.id + '/comentarios', 'POST', Object.fromEntries(new FormData(event.target)));
            commentPreviewCache.delete(selected.id);
            event.target.reset(); await comments(selected.id); message('Comentario guardado.', false, 'detail-message');
        });
    };
    $('delete-task').onclick = () => {
        if (!confirm('Eliminar la tarea #' + selected.id + ' y sus comentarios?')) return;
        act(async () => { await request(api + '/' + selected.id, 'DELETE'); $('detail-dialog').close(); await refresh(); message('Tarea eliminada.'); });
    };
    $('edit-task').onclick = () => openForm(selected);
    $('new-task').onclick = () => openForm();
    $('search').oninput = () => { limit = 40; render(); };
    $('more').onclick = () => { limit += 40; render(); };
    $('refresh').onclick = () => (session ? refresh() : start()).then(() => message('Lista actualizada.')).catch(error => message(error.message, true));
    document.querySelectorAll('[data-close]').forEach(button => button.onclick = () => $(button.dataset.close).close());
    document.querySelectorAll('[data-filter]').forEach(button => button.onclick = () => {
        filter = button.dataset.filter; limit = 40; $('list-title').textContent = button.textContent;
        document.querySelectorAll('[data-filter]').forEach(b => b.setAttribute('aria-pressed', String(b === button))); render();
    });
    function applySolicitante(username) {
        const user = domainUsers.get((username || '').trim().toLowerCase());
        if (!user) return;
        $('task-form').elements.solicitanteUsername.value = user.username || '';
        $('task-form').elements.solicitanteNombre.value = user.nombreVisible || '';
        $('task-form').elements.solicitanteFuero.value = user.fuero || '';
        $('solicitante-help').textContent = 'Solicitante obtenido desde AD.';
    }
    async function searchSolicitantes(query) {
        const clean = query.trim();
        const options = $('solicitante-options');
        if (clean.length < 2) {
            options.replaceChildren();
            $('solicitante-help').textContent = 'Escriba al menos 2 caracteres para buscar en AD.';
            return;
        }
        $('solicitante-help').textContent = 'Buscando usuarios de AD...';
        // La app movil no mantiene una copia de AD; solo consulta al servidor con sesion autenticada.
        const result = await request('api/v1/movil/usuarios-dominio?q=' + encodeURIComponent(clean));
        options.replaceChildren();
        domainUsers.clear();
        if (!result.disponible) {
            $('solicitante-help').textContent = result.mensaje || 'No se pudo consultar AD.';
            return;
        }
        for (const user of result.usuarios || []) {
            domainUsers.set((user.username || '').toLowerCase(), user);
            const option = element('option');
            option.value = user.username;
            option.label = [user.username, user.nombreVisible, user.fuero].filter(Boolean).join(' - ');
            options.append(option);
        }
        $('solicitante-help').textContent = result.usuarios.length ? 'Seleccione un usuario para completar nombre y fuero.' : 'No se encontraron usuarios.';
        applySolicitante($('task-form').elements.solicitanteUsername.value);
    }
    $('solicitante-username-input').addEventListener('input', event => {
        clearTimeout(domainTimer);
        domainTimer = setTimeout(() => searchSolicitantes(event.target.value).catch(error => {
            $('solicitante-help').textContent = error.message || 'No se pudo consultar AD.';
        }), 350);
    });
    $('solicitante-username-input').addEventListener('change', event => applySolicitante(event.target.value));
    $('solicitante-username-input').addEventListener('blur', event => applySolicitante(event.target.value));
    function beep() {
        if (!audio || audio.state !== 'running') return;
        const oscillator = audio.createOscillator(), gain = audio.createGain();
        oscillator.connect(gain); gain.connect(audio.destination); oscillator.frequency.value = 880;
        gain.gain.setValueAtTime(.12, audio.currentTime); gain.gain.exponentialRampToValueAtTime(.001, audio.currentTime + .45);
        oscillator.start(); oscillator.stop(audio.currentTime + .45);
    }
    $('sound').hidden = native;
    if (native && $('download-apk')) $('download-apk').hidden = true;
    $('sound').onclick = async () => {
        try {
            if (!audio) audio = new (window.AudioContext || window.webkitAudioContext)();
            await audio.resume(); sound = !sound;
            $('sound').setAttribute('aria-pressed', String(sound));
            const label = sound ? 'Silenciar esta pantalla' : 'Activar sonido en esta pantalla';
            $('sound').setAttribute('aria-label', label); $('sound').title = label;
            $('sound').replaceChildren();
            const icon = element('i'); icon.dataset.lucide = sound ? 'bell' : 'bell-off'; $('sound').append(icon); icons();
            if (sound) beep();
        } catch { message('El navegador no pudo activar el sonido.', true); }
    };
    async function poll() {
        if (stopped) return;
        try {
            const batch = await request('api/v1/movil/avisos' + (cursor != null ? '?despuesDe=' + cursor : ''));
            const incoming = batch.avisos.filter(a => a.autor?.toLowerCase() !== session.usuario.username.toLowerCase());
            if (incoming.length && !native) {
                message(incoming.length === 1 ? 'Nueva tarea: ' + incoming[0].titulo : incoming.length + ' tareas nuevas.');
                if (sound) beep();
            }
            cursor = batch.siguiente;
            try { localStorage.setItem(cursorKey, String(cursor)); } catch { /* El seguimiento sigue en memoria. */ }
            if (!document.querySelector('dialog[open]') && !busy) await refresh();
            $('connection').textContent = 'Conectado'; $('connection').classList.remove('offline');
        } catch {
            $('connection').textContent = 'Sin conexion. Reintentando...'; $('connection').classList.add('offline');
        } finally { if (!stopped) setTimeout(poll, 10000); }
    }
    async function start() {
        try {
            session = await request('api/v1/movil/sesion');
            $('username').textContent = session.usuario.nombreVisible + ' | ' + session.usuario.username;
            $('new-task').hidden = !session.puedeEditar;
            cursorKey = 'tareas.cursor.' + base + '.' + session.usuario.username;
            try { const value = localStorage.getItem(cursorKey); if (value !== null && /^\d+$/.test(value)) cursor = Number(value); } catch { /* Almacenamiento opcional. */ }
            await refresh();
            const id = Number(new URLSearchParams(location.search).get('tarea'));
            if (id) { const task = tasks.find(t => t.id === id); if (task) await openDetail(task); else message('La tarea solicitada ya no existe.', true); }
            poll();
        } catch (error) { message(error.message || 'No se pudo conectar. Recargue la pantalla.', true); $('connection').textContent = 'No conectado'; }
    }
    icons(); start();
})();
