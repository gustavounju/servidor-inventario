& {
# Inventario GOLD - Versión Silenciosa Completa para GPO (SYSTEM)
# V2.2 - Incluye Detección de Office, Monitores, Discos y Motherboard
# -----------------------------------------------------------

$ErrorActionPreference = "SilentlyContinue"
$logFile = "C:\Windows\Temp\inventario_gold.log"

function Write-Log {
    param($msg)
    "[" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "] $msg" | Out-File $logFile -Append
}

function e($s) { 
    if ($null -eq $s) { return "" }
    $val = [string]$s
    $val = $val -replace "\\", "\\\\"
    $val = $val -replace "`"", "\`""
    $val = $val -replace "`r", ""
    $val = $val -replace "`n", ""
    return $val
}

Write-Log "Iniciando recolección completa..."

# -----------------------------------------------------------
# CONFIGURACIÓN DE SEGURIDAD
# -----------------------------------------------------------
try {
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    add-type "using System.Net; using System.Security.Cryptography.X509Certificates; public class TrustAllCertsPolicy : ICertificatePolicy { public bool CheckValidationResult(ServicePoint srvPoint, X509Certificate certificate, WebRequest request, int certificateProblem) { return true; } }"
    [System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
} catch {}

# -----------------------------------------------------------
# RECOLECCIÓN DE DATOS
# -----------------------------------------------------------
try {
    $os = Get-WmiObject Win32_OperatingSystem
    $cs = Get-WmiObject Win32_ComputerSystem
    $cpu = Get-WmiObject Win32_Processor | Select-Object -First 1
    $mb = Get-WmiObject Win32_BaseBoard | Select-Object -First 1
    
    # Red
    $netCfg = Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled = True" | Select-Object -First 1
    $ip = if ($netCfg.IPAddress -is [array]) { $netCfg.IPAddress[0] } else { $netCfg.IPAddress }
    
    # RAM
    $ramGB = if ($cs.TotalPhysicalMemory) { [math]::Round($cs.TotalPhysicalMemory / 1GB, 2) } else { 0 }
    
    # Discos
    $diskModels = @()
    $diskDrives = Get-WmiObject Win32_DiskDrive
    foreach ($d in $diskDrives) {
        $size = [math]::Round($d.Size / 1GB, 0)
        $diskModels += "$($d.Model) ($($size)GB)"
    }
    $diskModelsStr = [string]::Join(" | ", $diskModels)

    # Monitores
    $monList = @()
    $monItems = Get-WmiObject -Namespace root\WMI -Class WmiMonitorID -ErrorAction SilentlyContinue
    if ($monItems) {
        foreach ($m in $monItems) {
            $mn = ""
            foreach ($c in $m.ManufacturerName) { if ($c -ne 0) { $mn += [char]$c } }
            $monList += $mn
        }
    }
    $monitorsStr = [string]::Join(" | ", $monList)

    # Versión de Office
    $officeVersion = "No detectado"
    try {
        $word = New-Object -ComObject Word.Application -ErrorAction SilentlyContinue
        if ($word) {
            $v = $word.Version
            $word.Quit()
            $map = @{"16.0"="2016/365"; "15.0"="2013"; "14.0"="2010"; "12.0"="2007"}
            $officeVersion = if ($map.ContainsKey($v)) { "Microsoft Office " + $map[$v] } else { "Microsoft Office " + $v }
        }
    } catch {}

    # Impresoras
    $allPrinters = Get-WmiObject Win32_Printer
    $bestPrinter = $allPrinters | Where-Object { $_.Default -eq $true } | Select-Object -First 1
    if (-not $bestPrinter -or $bestPrinter.Name -match "PDF|XPS|OneNote") {
        $bestPrinter = $allPrinters | Where-Object { $_.Name -notmatch "PDF|XPS|OneNote" } | Select-Object -First 1
    }
    
    $printerSN = "N/A"
    if ($bestPrinter) {
        $regPaths = @(
            "HKLM:\SYSTEM\CurrentControlSet\Control\Print\Printers\$($bestPrinter.Name)\PrinterDriverData",
            "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Print\Printers\$($bestPrinter.Name)\PrinterDriverData"
        )
        foreach ($rp in $regPaths) {
            if (Test-Path $rp) {
                $val = Get-ItemProperty $rp -Name "SerialNumber" -ErrorAction SilentlyContinue
                if ($val.SerialNumber) { $printerSN = $val.SerialNumber; break }
            }
        }
    }

    # -----------------------------------------------------------
    # CONSTRUCCIÓN DEL JSON COMPLETO
    # -----------------------------------------------------------
    $json = "{
        ""PC_Nombre"": ""$(e $env:COMPUTERNAME)"",
        ""Usuario_Actual"": ""$(e $env:USERNAME)"",
        ""Fecha_Reporte"": ""$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"",
        ""Sistema"": {
            ""OsName"": ""$(e $os.Caption)"",
            ""Procesador"": ""$(e $cpu.Name)"",
            ""RAM (GB)"": $ramGB,
            ""Office"": ""$(e $officeVersion)""
        },
        ""Red"": [{""IPAddress"": ""$ip"", ""MACAddress"": ""$($netCfg.MACAddress)""}],
        ""Motherboard_Model"": ""$(e $mb.Manufacturer) $(e $mb.Product)"",
        ""Disk_Models"": ""$(e $diskModelsStr)"",
        ""Monitors"": ""$(e $monitorsStr)"",
        ""Printer_Model"": ""$(e $bestPrinter.Name)"",
        ""Printer_Port"": ""$(e $bestPrinter.PortName)"",
        ""Printer_SN"": ""$(e $printerSN)"",
        ""Salud"": { ""Uptime_Dias"": 0 }
    }"

    # -----------------------------------------------------------
    # ENVÍO
    # -----------------------------------------------------------
    $servidor = "__INVENTARIO_SERVER_URL__/submit_inventory"
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("Content-Type", "application/json; charset=utf-8")
    $wc.Encoding = [System.Text.Encoding]::UTF8
    [void]$wc.UploadString($servidor, "POST", $json)
    
    Write-Log "Inventario COMPLETO enviado exitosamente."
} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
}
}
