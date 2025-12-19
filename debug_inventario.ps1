# --- Script de DEBUG Inventario (Verifica envío de datos) ---
$UrlBase = "http://localhost:5000"
$UrlInventario = "$UrlBase/submit_inventory"
$PC_Nombre = $env:COMPUTERNAME

Clear-Host
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   DIAGNOSTICO DE ENVIO - INVENTARIO" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Nombre de PC
Write-Host "[1] Verificando identidad del equipo..." -ForegroundColor Yellow
Write-Host "    Nombre detectado: '$PC_Nombre'" -ForegroundColor White
if ($PC_Nombre -ne "SISTEMAS-106") {
    Write-Warning "    ATENCION: El script detecta el nombre '$PC_Nombre', no 'SISTEMAS-106'."
}
else {
    Write-Host "    Nombre correcto." -ForegroundColor Green
}
Write-Host ""

# 2. Verificar Conectividad
Write-Host "[2] Probando conexión con el servidor ($UrlBase)..." -ForegroundColor Yellow
try {
    $test = Test-NetConnection -ComputerName 10.15.2.251 -Port 5000
    if ($test.TcpTestSucceeded) {
        Write-Host "    Conectividad TCP OK." -ForegroundColor Green
    }
    else {
        Write-Host "    FALLO DE CONEXION TCP." -ForegroundColor Red
        Write-Host "    No se puede contactar al servidor. Revisa red/firewall."
        exit
    }
}
catch {
    Write-Warning "    No se pudo ejecutar Test-NetConnection (¿PowerShell antiguo?). Saltando check..."
}
Write-Host ""

# 3. Generar Datos de Prueba (Simula el script real)
Write-Host "[3] Generando paquete de datos..." -ForegroundColor Yellow

# Datos básicos mínimos para prueba
$payload = @{
    PC_Nombre      = $PC_Nombre
    Usuario_Actual = $env:USERNAME
    Fecha_Reporte  = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Sistema        = @{
        OsName     = "Windows Debug Mode"
        Procesador = "CPU Genetico Debug"
        "RAM (GB)" = 8
    }
    RAM_Detalles   = "RAM Debug"
    Disk_Models    = "HDD Debug"
    Red            = @(@{ IPAddress = "127.0.0.1" })
    DEBUG_MODE     = $true
}

$json = $payload | ConvertTo-Json -Depth 5
Write-Host "    Datos a enviar (JSON Preview):" -ForegroundColor Gray
Write-Host $json -ForegroundColor Gray
Write-Host ""

# 4. Enviar al Servidor
Write-Host "[4] ENVIANDO AL SERVIDOR..." -ForegroundColor Yellow
try {
    $web = New-Object System.Net.WebClient
    $web.Headers.Add("Content-Type", "application/json")
    $web.Encoding = [System.Text.Encoding]::UTF8
    
    # Capturar respuesta
    $responseBytes = $web.UploadData($UrlInventario, "POST", [System.Text.Encoding]::UTF8.GetBytes($json))
    $responseString = [System.Text.Encoding]::UTF8.GetString($responseBytes)

    Write-Host "    ¡ENVIO EXITOSO!" -ForegroundColor Green
    Write-Host "    Respuesta del Servidor:" -ForegroundColor Cyan
    Write-Host "    $responseString" -ForegroundColor White
    
    if ($responseString -match "success") {
        Write-Host ""
        Write-Host "    CONCLUSION: El servidor recibió y aceptó los datos." -ForegroundColor Green
        Write-Host "    Si no ves la PC en la web, revisa el filtro de 'Activos/Inactivos' o busca por nombre."
    }
    else {
        Write-Host ""
        Write-Host "    ATENCION: El servidor respondió pero no dijo 'success'. Revisa el mensaje arriba." -ForegroundColor Magenta
    }

}
catch {
    Write-Host "    ERROR FATAL AL ENVIAR:" -ForegroundColor Red
    Write-Host "    $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        Write-Host "    DETALLE RESPUESTA HTTP:" -ForegroundColor Red
        Write-Host "    $($reader.ReadToEnd())" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Read-Host "Presiona ENTER para cerrar"
