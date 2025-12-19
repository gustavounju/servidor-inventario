# Inventario GOLD - Cliente
# Compatible con Windows 7 (PowerShell 2.0) y Windows 10/11
# V2.0 - Corrección para "ConvertTo-Json" y "Invoke-RestMethod"

# -----------------------------------------------------------
# CONFIGURACIÓN DE LOGGING (DEBUGGING)
# -----------------------------------------------------------
$ErrorActionPreference = "Continue"
$script:errorOccurred = $false
$tempLogFile = "$env:TEMP\Inventario_Log_$($env:COMPUTERNAME).txt"

try {
    Start-Transcript -Path $tempLogFile -Force -ErrorAction SilentlyContinue
}
catch {}

# -----------------------------------------------------------
# CONFIGURACIÓN PREVIA (SEGURIDAD Y RED)
# -----------------------------------------------------------
# Forzar TLS 1.2 (Protocolo 3072) usando casting para evitar error de parser en .NET viejos
try {
    # 3072 es el valor de Tls12. Usamos int para que no falle si el Enum no tiene el miembro definido.
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
}
catch {
    # Ignorar si falla, el sistema usará su default
}

# -----------------------------------------------------------
# FUNCIÓN: ConvertTo-JsonCustom (Polyfill para PS 2.0)
# -----------------------------------------------------------
function ConvertTo-JsonCustom($InputObject) {
    if ($InputObject -eq $null) { return "null" }
    
    $type = $InputObject.GetType()

    # Tipos numéricos y booleanos
    if ($InputObject -is [bool]) { return $InputObject.ToString().ToLower() }
    if ($InputObject -is [int] -or $InputObject -is [long] -or $InputObject -is [double] -or $InputObject -is [decimal] -or $InputObject -is [float]) {
        return $InputObject.ToString().Replace(",", ".")
    }

    # Strings (escapar caracteres especiales)
    if ($InputObject -is [string] -or $InputObject -is [char] -or $type.Name -eq "DateTime") { 
        # Chained .Replace en una sola linea para evitar error de parser en PS 2.0 si el backtick falla
        $str = $InputObject.ToString().Replace("\", "\\").Replace('"', '\"').Replace("`r", "\r").Replace("`n", "\n").Replace("`t", "\t")
        return "`"$str`""
    }

    # Arrays / Colecciones
    if ($InputObject -is [System.Collections.IEnumerable] -and $InputObject -isnot [System.Collections.IDictionary] -and $InputObject -isnot [string]) {
        $items = @()
        foreach ($item in $InputObject) {
            $items += ConvertTo-JsonCustom $item
        }
        return "[ " + ([string]::Join(", ", $items)) + " ]"
    }

    # Hashtables / Diccionarios
    if ($InputObject -is [System.Collections.IDictionary]) {
        $props = @()
        foreach ($key in $InputObject.Keys) {
            $val = ConvertTo-JsonCustom $InputObject[$key]
            $props += "`"$key`": $val"
        }
        return "{ " + ([string]::Join(", ", $props)) + " }"
    }
    
    # Objetos genéricos PSObject
    if ($InputObject -is [PSObject]) {
        $props = @()
        $properties = $InputObject | Get-Member -MemberType Properties
        foreach ($prop in $properties) {
            $name = $prop.Name
            $val = ConvertTo-JsonCustom $InputObject.$name
            $props += "`"$name`": $val"
        }
        return "{ " + ([string]::Join(", ", $props)) + " }"
    }

    # Fallback
    return "`"$($InputObject.ToString())`""
}

# -----------------------------------------------------------
# RECOLECCIÓN DE DATOS
# -----------------------------------------------------------


# -----------------------------------------------------------
# BLOQUE PRINCIPAL (GLOBAL TRY/CATCH)
# -----------------------------------------------------------
try {

    Write-Host "Recopilando datos..." -ForegroundColor Cyan


    # 1) Datos básicos de la PC
    $cs = Get-WmiObject -Class Win32_ComputerSystem
    $os = Get-WmiObject -Class Win32_OperatingSystem
    $cpu = Get-WmiObject -Class Win32_Processor | Select-Object -First 1

    $pcNombre = $env:COMPUTERNAME
    $usuarioActual = $env:USERNAME
    $fechaReporte = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    # RAM en GB
    $ramGB = 0
    if ($cs.TotalPhysicalMemory) {
        $ramGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2)
    }

    # 2) Red
    $ipAddress = "N/A"
    try {
        $ipObj = Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled = True" | Select-Object -First 1 -ExpandProperty IPAddress
        if ($ipObj -is [array]) { $ipAddress = $ipObj[0] } else { $ipAddress = $ipObj }
    }
    catch {}

    # 3) RAM Detalles
    $ramDetalles = "N/A"
    try {
        $ramModulos = Get-WmiObject -Class Win32_PhysicalMemory
        if ($ramModulos) {
            $detalles = @()
            foreach ($r in $ramModulos) {
                $cap = [math]::Round($r.Capacity / 1GB, 0)
                $detalles += "$($cap)GB @ $($r.Speed)MHz"
            }
            $ramDetalles = [string]::Join(" | ", $detalles)
        }
    }
    catch {}

    # 4) Discos
    $diskModelsStr = "N/A"
    $diskSpeedsStr = "N/A"
    try {
        $diskDrives = Get-WmiObject -Class Win32_DiskDrive
        if ($diskDrives) {
            $models = @()
            $speeds = @()
            foreach ($d in $diskDrives) {
                $size = [math]::Round($d.Size / 1GB, 0)
                $models += "$($d.Model) ($($size)GB)"
            
                if ($d.Model -match "SSD" -or $d.MediaType -eq "SSD") {
                    $speeds += "$($d.Model): SSD"
                }
                else {
                    $speeds += "$($d.Model): $($d.SpindleSpeed) RPM"
                }
            }
            $diskModelsStr = [string]::Join(" | ", $models)
            $diskSpeedsStr = [string]::Join(" | ", $speeds)
        }
    }
    catch {}

    # 5) Motherboard
    $motherboardModel = "N/A"
    try {
        $mb = Get-WmiObject -Class Win32_BaseBoard | Select-Object -First 1
        if ($mb) { $motherboardModel = "$($mb.Manufacturer) $($mb.Product)" }
    }
    catch {}

    # 6) Impresora
    $printerModel = "N/A"
    $printerPort = "N/A"
    try {
        # WMI Win32_Printer funciona en Win7
        $defaultPrinter = Get-WmiObject -Class Win32_Printer | Where-Object { $_.Default -eq $true } | Select-Object -First 1
        if ($defaultPrinter) {
            $printerModel = $defaultPrinter.Name
            $printerPort = $defaultPrinter.PortName

            # Detectar tipo de puerto
            if ($printerPort -like "USB*" -or $printerPort -like "LPT*") { 
                $printerPort += " (Local)" 
            }
            elseif ($printerPort -like "*IP_*" -or $printerPort -like "WSD-*" -or $printerPort -like "\\*") { 
                $printerPort += " (Red)" 
            }
        }
    }
    catch {}

    # 7) Monitores (WmiMonitorID a veces falla en Win7 si no hay permisos, try-catch)
    $monitorsStr = "N/A"
    try {
        $monItems = Get-WmiObject -Namespace root\WMI -Class WmiMonitorID -ErrorAction SilentlyContinue
        if ($monItems) {
            $mList = @()
            foreach ($m in $monItems) {
                # Convertir array de ints a string chars manual
                $mn = ""
                if ($m.ManufacturerName) { 
                    foreach ($c in $m.ManufacturerName) { if ($c -ne 0) { $mn += [char]$c } } 
                }
                $mList += $mn
            }
            $monitorsStr = [string]::Join(" | ", $mList)
        }
    }
    catch {}

    # -----------------------------------------------------------
    # CONSTRUCCIÓN DEL PAYLOAD
    # -----------------------------------------------------------

    $payload = @{
        "PC_Nombre"         = $pcNombre
        "Usuario_Actual"    = $usuarioActual
        "Fecha_Reporte"     = $fechaReporte
    
        "Sistema"           = @{
            "OsName"     = $os.Caption
            "Procesador" = $cpu.Name
            "RAM (GB)"   = $ramGB
        }

        "Red"               = @(
            @{ "IPAddress" = $ipAddress }
        )

        "RAM_Detalles"      = $ramDetalles
        "Disk_Models"       = $diskModelsStr
        "Disk_Speeds_RPM"   = $diskSpeedsStr
        "Motherboard_Model" = $motherboardModel
        "Printer_Model"     = $printerModel
        "Printer_Port"      = $printerPort
        "Monitors"          = $monitorsStr
    }

    # -----------------------------------------------------------
    # CONVERSIÓN A JSON (DETECTAR VERSIÓN)
    # -----------------------------------------------------------
    $json = ""

    # Verificar si existe ConvertTo-Json (PowerShell 3.0+)
    if (Get-Command "ConvertTo-Json" -ErrorAction SilentlyContinue) {
        Write-Host "Usando ConvertTo-Json nativo..."
        $json = $payload | ConvertTo-Json -Depth 5
    }
    else {
        Write-Host "Usando función JSON personalizada (Modo PS 2.0)..."
        $json = ConvertTo-JsonCustom $payload
    }

    # -----------------------------------------------------------
    # ENVÍO AL SERVIDOR (WEBCLIENT PARA COMPATIBILIDAD)
    # -----------------------------------------------------------
    $servidor = "http://localhost:5000/submit_inventory"
    Write-Host "Enviando a $servidor ..."

    try {
        # Usamos System.Net.WebClient porque Invoke-RestMethod no existe en PS 2.0
        $wc = New-Object System.Net.WebClient
        $wc.Headers.Add("Content-Type", "application/json; charset=utf-8")
        $wc.Encoding = [System.Text.Encoding]::UTF8
    
        $response = $wc.UploadString($servidor, "POST", $json)
    
        Write-Host "Inventario enviado EXITOSAMENTE." -ForegroundColor Green
    }
    catch {
        $script:errorOccurred = $true
        Write-Host "ERROR al enviar el inventario:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    
        # Mostrar detalle si es WebException
        if ($_.Exception.InnerException) {
            Write-Host $_.Exception.InnerException.Message -ForegroundColor DarkRed
        }

    
        # Backup Local de JSON en Escritorio
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $backupJson = "$desktopPath\Inventario_$pcNombre.json"
    
        try {
            [System.IO.File]::WriteAllText($backupJson, $json)
            Write-Host "Se guardó el JSON del inventario en: $backupJson" -ForegroundColor Yellow
        }
        catch {
            Write-Host "No se pudo guardar copia local del JSON." -ForegroundColor DarkRed
        }
    }

    # -----------------------------------------------------------
    # FINALIZAR LOGGING Y GUARDAR SI HUBO ERROR
    # -----------------------------------------------------------
    # Stop Transcript dentro del try
    Stop-Transcript -ErrorAction SilentlyContinue

}
catch {
    $script:errorOccurred = $true
    Write-Host "ERROR CRITICO GLOBAL:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
}

# -----------------------------------------------------------
# FINALIZAR Y GUARDAR LOG
# -----------------------------------------------------------


if ($script:errorOccurred) {
    try {
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $destLog = "$desktopPath\Log_Error_$($env:COMPUTERNAME).txt"
        Copy-Item -Path $tempLogFile -Destination $destLog -Force
        
        # Re-abrir consola para avisar usuario (aunque transcript ya cerró)
        Write-Host "---------------------------------------------------" -ForegroundColor Red
        Write-Host "Ocurrió un error. Se ha guardado el LOG completo en:" -ForegroundColor Yellow
        Write-Host "$destLog" -ForegroundColor Yellow
        Write-Host "Por favor envíe este archivo al administrador." -ForegroundColor Yellow
        Write-Host "---------------------------------------------------" -ForegroundColor Red
    }
    catch {
        # Nada que hacer si falla la copia
    }
}

Start-Sleep -Seconds 10
