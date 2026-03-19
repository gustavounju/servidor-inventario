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

function onFilterClick(param, value) {
    const url = new URL(window.location.href);
    url.searchParams.set(param, value);
    window.location.href = url.toString();
}

function copyScript(btn) {
    const urlHttps = btn.getAttribute('data-url-https');
    const urlHttp = btn.getAttribute('data-url-http');
    
    const command = `Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; $u1='${urlHttps}'; $u2='${urlHttp}'; try { iwr $u1 -OutFile $env:TEMP\\i.ps1 -TimeoutSec 5 } catch { iwr $u2 -OutFile $env:TEMP\\i.ps1 }; if (Test-Path $env:TEMP\\i.ps1) { & $env:TEMP\\i.ps1 }`;
    
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

// Initialize theme on load
(function() {
    const savedTheme = localStorage.getItem('theme') || 'oceanic';
    document.documentElement.setAttribute('data-theme', savedTheme);
})();
