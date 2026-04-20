/**
 * gold.js — Shared logic for Inventario GOLD
 * Includes Theme Management and common UI actions.
 */

function setTheme(themeName) {
    document.documentElement.setAttribute('data-theme', themeName);
    localStorage.setItem('theme', themeName);
    
    // Update SIGJ dots if they exist
    const dots = document.querySelectorAll('.sigj-dot');
    dots.forEach(dot => {
        // Theme specific tweaks can go here if needed
    });
}

function onFilterClick(type) {
    let url;
    // Si estamos en cualquier otra página (ej. /infra/ o /reportes/), redirigir al Dashboard (/)
    if (window.location.pathname !== '/' && window.location.pathname !== '/cementerio') {
        url = new URL(window.location.protocol + "//" + window.location.host + "/");
    } else {
        url = new URL(window.location.href);
    }

    const currentAlerta = url.searchParams.get('alerta');
    const currentOs = url.searchParams.get('os');
    const currentTasks = url.searchParams.get('filter_tasks');

    // Reset page param on new filter
    url.searchParams.set('page', 1);

    // Clear existing specific filters to allow toggling/switching
    url.searchParams.delete('alerta');
    url.searchParams.delete('os');
    url.searchParams.delete('filter_tasks');

    // Toggle logic: Si se hizo click en el que NO estaba activo, se activa.
    // Si estaba activo (toggle-off), se quitó arriba y quedará limpio.
    if (type === 'ram' && currentAlerta !== 'ram') {
        url.searchParams.set('alerta', 'ram');
    } else if (type === 'sin_impresora' && currentAlerta !== 'sinimp') {
        url.searchParams.set('alerta', 'sinimp');
    } else if (type === 'solo_red' && currentAlerta !== 'red') {
        url.searchParams.set('alerta', 'red');
    } else if (type === 'win7' && currentOs !== 'win7') {
        url.searchParams.set('os', 'win7');
    } else if (type === 'win10' && currentOs !== 'win10') {
        url.searchParams.set('os', 'win10');
    } else if (type === 'win11' && currentOs !== 'win11') {
        url.searchParams.set('os', 'win11');
    } else if (type === 'tareas' && currentTasks !== 'true') {
        url.searchParams.set('filter_tasks', 'true');
    }

    // Always ensure active PCs (except for Graveyard which is a link)
    if (window.location.href.includes('estado=False') && !url.searchParams.has('estado')) {
        url.searchParams.set('estado', 'False');
    } else if (!url.searchParams.has('estado')) {
        // Only force True if we aren't deliberately going to Graveyard
        url.searchParams.set('estado', 'True');
    }

    window.location.href = url.toString();
}

function copyScript(btn) {
    const urlHttps = btn.getAttribute('data-url-https');
    const urlHttp = btn.getAttribute('data-url-http');
    
    // Add SSL bypass and use DownloadString like in the /install page
    const command = `Set-ExecutionPolicy Bypass -Scope Process -Force; try { [Net.ServicePointManager]::SecurityProtocol = 3072 } catch {}; try { Add-Type -TypeDefinition 'using System.Net; using System.Security.Cryptography.X509Certificates; public class T : ICertificatePolicy { public bool CheckValidationResult(ServicePoint s, X509Certificate c, WebRequest r, int p) { return true; } }' } catch {}; [System.Net.ServicePointManager]::CertificatePolicy = New-Object T; try { iex (New-Object System.Net.WebClient).DownloadString('${urlHttps}') } catch { Write-Host 'Fallo HTTPS, intentando HTTP alternativo...' -ForegroundColor Yellow; iex (New-Object System.Net.WebClient).DownloadString('${urlHttp}') };\r\n\r\n\r\n`;
    
    navigator.clipboard.writeText(command).then(() => {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check-all"></i> <span>¡Copiado!</span>';
        btn.classList.add('text-success');
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.classList.remove('text-success');
        }, 2000);
    });
}

// ===== Buscador Global (Header) =====
document.addEventListener('DOMContentLoaded', function () {
    // Buscar el input de búsqueda de forma más robusta
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) {
        console.warn("Inventario GOLD: searchInput no encontrado.");
        return;
    }

    let searchDebounce = null;
    let currentSearchQuery = searchInput.value;
    let ajaxAbortController = null;

    searchInput.addEventListener('input', function () {
        const query = searchInput.value.trim();
        const filter = query.toLowerCase();
        const table = document.getElementById('inventoryTable');
        
        // 1. Filtrado Local Instantáneo
        if (table) {
            const rows = table.querySelectorAll('tbody tr:not(.no-results-row)');
            let visibleCount = 0;
            rows.forEach(function (tr) {
                // Buscamos en el texto de la fila y también en atributos data si existen
                const text = tr.textContent.toLowerCase();
                const so = (tr.getAttribute('data-so') || '').toLowerCase();
                const isMatch = text.indexOf(filter) > -1 || so.indexOf(filter) > -1;
                
                tr.style.display = isMatch ? '' : 'none';
                if (isMatch) visibleCount++;
            });

            // Si no hay locales visibles y hay filtro, mostrar aviso
            let noResultsRow = table.querySelector('.no-results-row');
            if (visibleCount === 0 && filter.length > 0) {
                if (!noResultsRow) {
                    const tbody = table.querySelector('tbody');
                    const colCount = table.querySelectorAll('thead th').length;
                    noResultsRow = document.createElement('tr');
                    noResultsRow.className = 'no-results-row';
                    noResultsRow.innerHTML = `<td colspan="${colCount}" class="text-center py-4 text-muted"> <i class="bi bi-search me-2"></i> No se encontraron resultados locales. Buscando...</td>`;
                    tbody.appendChild(noResultsRow);
                }
            } else if (noResultsRow) {
                noResultsRow.remove();
            }
        }

        // 2. Búsqueda Global AJAX (Debounced)
        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(() => {
            if (searchInput.value.trim() === currentSearchQuery) return;
            currentSearchQuery = searchInput.value.trim();
            console.log("Inventario GOLD: Iniciando búsqueda en vivo para:", currentSearchQuery);
            executeGlobalSearchAjax(currentSearchQuery);
        }, 400); 
    });

    async function executeGlobalSearchAjax(q) {
        const tableContainer = document.getElementById('inventoryTableContainer');
        const spinner = document.querySelector('.search-spinner');
        const defIcon = document.querySelector('.search-icon-default');
        
        if (!tableContainer) return; 

        // Abortar búsqueda anterior si está en curso
        if (ajaxAbortController) {
            ajaxAbortController.abort();
        }
        ajaxAbortController = new AbortController();

        const url = new URL(window.location.href);
        const isDashboard = window.location.pathname === '/' || window.location.pathname.includes('dashboard');
        
        if (!isDashboard) {
            console.log("Inventario GOLD: Live search omitido (fuera de Dashboard).");
            return;
        }

        url.searchParams.set('q', q);
        url.searchParams.set('page', 1);

        // Mostrar Spinner
        if (spinner && defIcon) {
            spinner.classList.remove('d-none');
            defIcon.classList.add('d-none');
        }

        try {
            const response = await fetch(url.toString(), {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                signal: ajaxAbortController.signal
            });

            if (!response.ok) throw new Error("Server error: " + response.status);

            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            const newTable = doc.getElementById('inventoryTableContainer');
            if (newTable) {
                // Efecto visual de actualización (flash amarillo)
                tableContainer.style.transition = 'background-color 0.3s';
                tableContainer.style.backgroundColor = 'rgba(255, 243, 205, 0.5)';
                
                tableContainer.innerHTML = newTable.innerHTML;
                
                setTimeout(() => {
                    tableContainer.style.backgroundColor = '';
                }, 400);

                if (isCompactMode) {
                    tableContainer.querySelectorAll('tbody tr td').forEach(td => {
                        td.style.padding = '0.4rem 0.5rem';
                    });
                }
            }

            // Actualizar Paginación
            const oldPag = document.getElementById('mainPagination');
            const newPag = doc.getElementById('mainPagination');
            if (oldPag && newPag) {
                oldPag.outerHTML = newPag.outerHTML;
            } else if (oldPag) {
                oldPag.style.display = 'none';
            } else if (newPag) {
                tableContainer.after(newPag);
            }

            window.history.replaceState({ path: url.toString() }, '', url.toString());

        } catch (err) {
            if (err.name === 'AbortError') {
                console.log("Inventario GOLD: Búsqueda abortada (nueva en curso).");
            } else {
                console.error('Inventario GOLD: Error en búsqueda en vivo:', err);
            }
        } finally {
            if (spinner && defIcon) {
                spinner.classList.add('d-none');
                defIcon.classList.remove('d-none');
            }
        }
    }
});

// ===== Exportar CSV Filtrado =====
function exportToCSV() {
    const table = document.getElementById('inventoryTable');
    if (!table) return;
    
    const rows = Array.from(table.querySelectorAll('tbody tr')).filter(row => row.style.display !== 'none');
    let csv = [];

    // Headers
    const headers = Array.from(table.querySelectorAll('thead th')).map(th =>
        th.textContent.trim().replace(/ ↑| ↓/g, '')
    );
    csv.push(headers.join(','));

    // Datos visibles
    rows.forEach(row => {
        const cols = Array.from(row.querySelectorAll('td')).map(td => {
            let text = td.textContent.trim();
            if (text.includes(',') || text.includes('"')) {
                text = '"' + text.replace(/"/g, '""') + '"';
            }
            return text;
        });
        csv.push(cols.join(','));
    });

    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'inventario_filtrado_' + new Date().toISOString().slice(0, 10) + '.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// ===== Modo Compacto/Expandido =====
let isCompactMode = localStorage.getItem('compactMode') === 'true';

function toggleCompactMode() {
    const table = document.getElementById('inventoryTable');
    if (!table) return;
    
    isCompactMode = !isCompactMode;
    const rows = table.querySelectorAll('tbody tr');

    if (isCompactMode) {
        table.style.fontSize = '0.75rem';
        rows.forEach(row => {
            row.querySelectorAll('td').forEach(td => {
                td.style.padding = '0.4rem 0.5rem';
            });
        });
    } else {
        table.style.fontSize = '';
        rows.forEach(row => {
            row.querySelectorAll('td').forEach(td => {
                td.style.padding = '';
            });
        });
    }

    localStorage.setItem('compactMode', isCompactMode);
    
    const icon = document.querySelector('#toggleCompactBtn i');
    if (icon) {
        icon.className = isCompactMode ? 'bi bi-distribute-vertical' : 'bi bi-list-ul';
    }
}

// Initialize theme and compact mode on load
(function() {
    const savedTheme = localStorage.getItem('theme') || 'oceanic';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    if (isCompactMode) {
        document.addEventListener('DOMContentLoaded', () => {
            // Re-apply if table exists
            const table = document.getElementById('inventoryTable');
            if (table) {
                isCompactMode = !isCompactMode; // Toggle back then run toggle to apply
                toggleCompactMode();
            }
        });
    }
})();
