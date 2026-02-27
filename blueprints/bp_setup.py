from flask import Blueprint, request, send_file
from io import BytesIO
import platform

bp_setup = Blueprint('setup', __name__)

@bp_setup.route("/script")
def get_script():
    """Devuelve el contenido del script inventario.ps1 modificado con la IP actual para ser copiado."""
    try:
        with open("inventario.ps1", "r", encoding="utf-8") as f:
            content = f.read()
        
        # El dashboard se sirve en 443 (o 80), pero el receiver de PS está siempre en 5000.
        # request.host_url devuelve "https://10.15.2.251/" si entras por 443, lo que rompe el script.
        # Vamos a asegurar que la IP/Host sea la actual, y usar el esquema correcto
        # según el entorno: Windows = Desarrollo (HTTP), Linux = Producción (HTTPS)
        current_host = request.host.split(':')[0] # Obtiene solo "10.15.2.251"
        scheme = "http" if platform.system() == "Windows" else "https"
        current_base_url = f"{scheme}://{current_host}:5000"
        
        modified_content = content.replace("https://10.15.2.251:5000", current_base_url)
        modified_content = modified_content.replace("http://10.15.2.251:5000", current_base_url)
        # Por si en el archivo estaba localhost
        modified_content = modified_content.replace("https://localhost:5000", current_base_url)
        modified_content = modified_content.replace("http://localhost:5000", current_base_url)
        
        mem = BytesIO()
        mem.write(modified_content.encode("utf-8"))
        mem.seek(0)
        
        return send_file(mem, mimetype="text/plain", as_attachment=False, download_name="inventario.ps1")
    except Exception as e:
        return f"Error al leer script: {e}", 500

@bp_setup.route("/install")
def install_page():
    """Página simple para descargar los scripts del cliente."""
    current_host = request.host.split(':')[0]
    scheme = "http" if platform.system() == "Windows" else "https"
    
    return f"""
    <html>
    <head>
        <title>Instalar Inventario</title>
        <style>
            body {{ font-family: sans-serif; padding: 40px; max-width: 600px; margin: 0 auto; background: #f8f9fa; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            h1 {{ color: #0d6efd; margin-top: 0; }}
            a.btn {{ display: block; background: #0d6efd; color: white; padding: 15px; text-decoration: none; border-radius: 5px; margin: 10px 0; text-align: center; font-weight: bold; }}
            a.btn:hover {{ background: #0b5ed7; }}
            .step {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📥 Instalación Cliente</h1>
            <p>Sigue estos pasos en la PC que quieres inventariar (Windows 7/10/11):</p>
            
            <div class="step">
                <strong>1. Crea una carpeta</strong> en el Escritorio llamada <code>Inventario</code>.
            </div>

            <div class="step">
                <strong>2. Descarga los archivos</strong> en esa carpeta:
                <a href="/download/script" class="btn">📄 1. Descargar Script (inventario.ps1)</a>
                <a href="/download/launcher" class="btn">🚀 2. Descargar Ejecutable (ejecutar_inventario.bat)</a>
            </div>

            <div class="step">
                <strong>3. Ejecuta</strong> el archivo <code>ejecutar_inventario.bat</code> (doble clic).
            </div>
            
            <hr>
            <p><small>Si Windows protege la PC, pulsa "Más información" -> "Ejecutar de todas formas".</small></p>
        </div>
        
        <div class="card" style="background-color: #e9ecef;">
            <h2 style="color: #495057; font-size: 1.2rem; margin-top:0;">⚡ Método Rápido (Antiguo)</h2>
            <p style="font-size: 0.9rem; color: #6c757d;">Para técnicos: Ejecuta el inventario sin descargar archivos. Abre <b>PowerShell como Administrador</b>, copia este comando y presiona Enter:</p>
            <div style="background: #212529; color: #20c20e; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 0.85rem; word-break: break-all; margin-bottom: 15px;">
                try {{ [Net.ServicePointManager]::SecurityProtocol = 3072 }} catch {{}}; try {{ Add-Type -TypeDefinition 'using System.Net; using System.Security.Cryptography.X509Certificates; public class T : ICertificatePolicy {{ public bool CheckValidationResult(ServicePoint s, X509Certificate c, WebRequest r, int p) {{ return true; }} }}' }} catch {{}}; [System.Net.ServicePointManager]::CertificatePolicy = New-Object T; try {{ iex (New-Object System.Net.WebClient).DownloadString('{scheme}://{current_host}:5000/script') }} catch {{ Write-Host 'Fallo HTTPS, intentando HTTP (Puerto 8080)...' -ForegroundColor Yellow; iex (New-Object System.Net.WebClient).DownloadString('http://{current_host}:8080/script') }}
            </div>
            <button onclick="copyCommand()" style="background: #6c757d; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; font-size: 0.9rem;">Copiar Comando</button>
            <span id="copyMsg" style="color: green; margin-left: 10px; display: none;">¡Copiado!</span>
            <script>
                function copyCommand() {{
                    const cmd = "try {{ [Net.ServicePointManager]::SecurityProtocol = 3072 }} catch {{}}; try {{ Add-Type -TypeDefinition 'using System.Net; using System.Security.Cryptography.X509Certificates; public class T : ICertificatePolicy {{ public bool CheckValidationResult(ServicePoint s, X509Certificate c, WebRequest r, int p) {{ return true; }} }}' }} catch {{}}; [System.Net.ServicePointManager]::CertificatePolicy = New-Object T; try {{ iex (New-Object System.Net.WebClient).DownloadString('" + window.location.protocol + "//" + window.location.hostname + ":5000/script') }} catch {{ Write-Host 'Fallo HTTPS, intentando HTTP (Puerto 8080)...' -ForegroundColor Yellow; iex (New-Object System.Net.WebClient).DownloadString('http://" + window.location.hostname + ":8080/script') }}\\n";
                    if (navigator.clipboard && window.isSecureContext) {{
                        navigator.clipboard.writeText(cmd).then(showCopied);
                    }} else {{
                        // Fallback fallback for non-https 
                        let textArea = document.createElement("textarea");
                        textArea.value = cmd;
                        textArea.style.position = "fixed";
                        textArea.style.left = "-999999px";
                        textArea.style.top = "-999999px";
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        try {{
                            document.execCommand('copy');
                            showCopied();
                        }} catch (err) {{
                            console.error('Fallback copy failed', err);
                        }}
                        textArea.remove();
                    }}
                }}
                function showCopied() {{
                    const msg = document.getElementById('copyMsg');
                    msg.style.display = 'inline';
                    setTimeout(() => msg.style.display = 'none', 2000);
                }}
            </script>
        </div>
    </body>
    </html>
    """

@bp_setup.route("/download/script")
def download_client_script():
    try:
        with open("inventario.ps1", "r", encoding="utf-8") as f:
            content = f.read()
            
        current_host = request.host.split(':')[0]
        scheme = "http" if platform.system() == "Windows" else "https"
        current_base_url = f"{scheme}://{current_host}:5000"
        
        modified_content = content.replace("https://10.15.2.251:5000", current_base_url)
        modified_content = modified_content.replace("http://10.15.2.251:5000", current_base_url)
        modified_content = modified_content.replace("https://localhost:5000", current_base_url)
        modified_content = modified_content.replace("http://localhost:5000", current_base_url)
        
        mem = BytesIO()
        mem.write(modified_content.encode("utf-8"))
        mem.seek(0)
        
        return send_file(mem, as_attachment=True, download_name="inventario.ps1")
    except Exception as e:
        return f"Error: {e}", 404

@bp_setup.route("/download/launcher")
def download_client_launcher():
    try:
        return send_file("ejecutar_inventario.bat", as_attachment=True, download_name="ejecutar_inventario.bat")
    except Exception as e:
        return f"Error: {e}", 404

@bp_setup.route("/download-cert")
def download_certificate():
    """Permite descargar el certificado SSL para instalarlo en dispositivos móviles."""
    try:
        return send_file(
            "cert.pem",
            as_attachment=True,
            download_name="inventario-cert.crt",
            mimetype="application/x-x509-ca-cert"
        )
    except Exception as e:
        return f"Error: {e}", 404
