# Inventario GOLD - Cliente
# Compatible con Windows 7 y Windows 10

# 1) Datos básicos de la PC
$cs  = Get-WmiObject -Class Win32_ComputerSystem
$os  = Get-WmiObject -Class Win32_OperatingSystem
$cpu = Get-WmiObject -Class Win32_Processor | Select-Object -First 1

$pcNombre      = $env:COMPUTERNAME
$usuarioActual = $env:USERNAME
$fechaReporte  = Get-Date

# RAM en GB (aprox)
$ramGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2)

# 2) Red: primera IP IPv4 válida
try {
    $ipObj = Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled = True" |
             Select-Object -First 1 -ExpandProperty IPAddress
    $ipAddress = ($ipObj | Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' } | Select-Object -First 1)
} catch {
    $ipAddress = "N/A"
}

# 3) RAM_Detalles: módulos de memoria
$ramModulos = Get-WmiObject -Class Win32_PhysicalMemory | ForEach-Object {
    "$($_.Capacity/1GB)GB @ $($_.Speed)MHz ($($_.Manufacturer) $($_.PartNumber.Trim()))"
}
$ramDetalles = if ($ramModulos) { $ramModulos -join " | " } else { "N/A" }

# 4) Discos: modelos y RPM (si están)
$diskDrives = Get-WmiObject -Class Win32_DiskDrive
$diskModels = $diskDrives | ForEach-Object {
    "$($_.Model) ($([math]::Round($_.Size/1GB,0))GB)"
}
$diskModelsStr = if ($diskModels) { $diskModels -join " | " } else { "N/A" }

$diskSpeeds = $diskDrives | ForEach-Object {
    if ($_.Capabilities -contains 4) {
        # 4 = supports SMART, no RPM; dejamos vacío o "SSD"
        "$($_.Model): SSD"
    } else {
        "$($_.Model): $($_.SpindleSpeed) RPM"
    }
}
$diskSpeedsStr = if ($diskSpeeds) { $diskSpeeds -join " | " } else { "N/A" }

# 5) Motherboard
$mb = Get-WmiObject -Class Win32_BaseBoard | Select-Object -First 1
$motherboardModel = if ($mb) { "$($mb.Manufacturer) $($mb.Product)" } else { "N/A" }

# 6) Impresora por defecto
$defaultPrinter = Get-WmiObject -Class Win32_Printer | Where-Object { $_.Default -eq $true } | Select-Object -First 1
if ($defaultPrinter) {
    $printerModel = $defaultPrinter.Name
    $printerPort  = $defaultPrinter.PortName
} else {
    $printerModel = "N/A"
    $printerPort  = "N/A"
}

# 7) Monitores (descripción sencilla)
$monitors = Get-WmiObject -Namespace root\WMI -Class WmiMonitorID -ErrorAction SilentlyContinue | ForEach-Object {
    $mn = ($_.ManufacturerName -ne 0 | ForEach-Object {[char]$_}) -join ''
    $pn = ($_.ProductCodeID      -ne 0 | ForEach-Object {[char]$_}) -join ''
    if (-not $mn) { $mn = "N/A" }
    if (-not $pn) { $pn = "N/A" }
    "$mn-$pn"
}
$monitorsStr = if ($monitors) { $monitors -join " | " } else { "N/A" }

# 8) Construir el objeto que espera el servidor
$payload = @{
    PC_Nombre     = $pcNombre
    Usuario_Actual= $usuarioActual
    Fecha_Reporte = $fechaReporte

    Sistema = @{
        OsName     = $os.Caption
        Procesador = $cpu.Name
        "RAM (GB)" = $ramGB
    }

    Red = @(
        @{
            IPAddress = $ipAddress
        }
    )

    RAM_Detalles     = $ramDetalles
    Disk_Models      = $diskModelsStr
    Disk_Speeds_RPM  = $diskSpeedsStr
    Motherboard_Model= $motherboardModel
    Printer_Model    = $printerModel
    Printer_Port     = $printerPort
    Monitors         = $monitorsStr
}

$json = $payload | ConvertTo-Json -Depth 5

# 9) Enviar al servidor
$servidor = "http://10.15.2.251:5000/submit_inventory"  # <-- IP del servidor Ubuntu

try {
    $resp = Invoke-RestMethod -Uri $servidor -Method Post -Body $json -ContentType "application/json" -TimeoutSec 10
    Write-Host ("Inventario enviado correctamente para {0}" -f $pcNombre) -ForegroundColor Green
} catch {
    Write-Host ("Error enviando inventario para {0}: {1}" -f $pcNombre, $_.Exception.Message) -ForegroundColor Red
}


