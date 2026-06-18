& {
# Inventario GOLD - Versión Silenciosa Completa para GPO (SYSTEM)
# V2.3 - Sincronizado con lógica probada de impresoras y hardware
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

Write-Log "Iniciando recolección sincronizada..."

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

    # Office
    $officeVersion = "No detectado"
    try {
        $word = New-Object -ComObject Word.Application -ErrorAction SilentlyContinue
        if ($word) { $officeVersion = "Microsoft Office " + $word.Version; $word.Quit() }
    } catch {}

    # -----------------------------------------------------------
    # LÓGICA DE IMPRESORAS (COPIADA DE INVENTARIO.PS1 PROBADO)
    # -----------------------------------------------------------
    $printerModel = "N/A"
    $printerPort = "N/A"
    $printerSN = "N/A"
    try {
        $allPrinters = Get-WmiObject -Class Win32_Printer
        $virtualKeywords = "PDF|XPS|OneNote|Fax|Send To|Microsoft Print|Writer"
        $bestPrinter = $allPrinters | Where-Object { $_.Default -eq $true } | Select-Object -First 1
        
        if (-not $bestPrinter -or $bestPrinter.Name -match $virtualKeywords) {
            $bestPrinter = $allPrinters | Where-Object { $_.Name -notmatch $virtualKeywords } | Select-Object -First 1
        }

        if ($bestPrinter) {
            $printerModel = $bestPrinter.Name
            $printerPort = $bestPrinter.PortName

            # RESOLUCIÓN DE WSD A IP
            if ($printerPort -like "WSD-*") {
                try {
                    $regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Print\Monitors\WSD Port\Ports\$($bestPrinter.PortName)"
                    if (Test-Path $regPath) {
                        $pUuid = (Get-ItemProperty $regPath)."Printer UUID"
                        if ($pUuid) {
                            $dafPath = "HKLM:\SYSTEM\CurrentControlSet\Enum\SWD\DAFWSDProvider\urn:uuid:$pUuid"
                            $locInfo = (Get-ItemProperty $dafPath -ErrorAction SilentlyContinue).LocationInformation
                            if ($locInfo -and $locInfo -match "https?://([^:/]+)") { $printerPort = $matches[1] }
                        }
                    }
                } catch {}
            }

            # RESOLUCIÓN PROACTIVA DE IP (DNS/mDNS)
            if ($printerPort -notmatch "^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$" -and $printerPort -notmatch "^(USB|LPT|COM|DOT4|FILE|PORTPROMPT|NUL|WSD-|\\)") {
                try {
                    $hostIps = [System.Net.Dns]::GetHostAddresses($printerPort)
                    if ($hostIps) { $printerPort = ($hostIps | Where-Object { $_.AddressFamily.ToString() -eq "InterNetwork" } | Select-Object -First 1).IPAddressToString }
                } catch {}
            }

            # DETECCIÓN DE SERIAL (USB/Registry)
            $regPaths = @(
                "HKLM:\SYSTEM\CurrentControlSet\Control\Print\Printers\$printerModel\PrinterDriverData",
                "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Print\Printers\$printerModel\PrinterDriverData"
            )
            foreach ($rp in $regPaths) {
                if (Test-Path $rp) {
                    $val = Get-ItemProperty $rp -ErrorAction SilentlyContinue
                    if ($val.SerialNumber) { $printerSN = $val.SerialNumber; break }
                    if ($val.SSN) { $printerSN = $val.SSN; break }
                }
            }
        }
    } catch {}

    # -----------------------------------------------------------
    # ENVÍO
    # -----------------------------------------------------------
    $json = "{
        ""PC_Nombre"": ""$(e $env:COMPUTERNAME)"",
        ""Usuario_Actual"": ""$(e $env:USERNAME)"",
        ""Fecha_Reporte"": ""$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"",
        ""Sistema"": { ""OsName"": ""$(e $os.Caption)"", ""Procesador"": ""$(e $cpu.Name)"", ""RAM (GB)"": $ramGB, ""Office"": ""$(e $officeVersion)"" },
        ""Red"": [{""IPAddress"": ""$ip"", ""MACAddress"": ""$($netCfg.MACAddress)""}],
        ""Motherboard_Model"": ""$(e $mb.Manufacturer) $(e $mb.Product)"",
        ""Disk_Models"": ""$(e $diskModelsStr)"",
        ""Monitors"": ""$(e $monitorsStr)"",
        ""Printer_Model"": ""$(e $printerModel)"",
        ""Printer_Port"": ""$(e $printerPort)"",
        ""Printer_SN"": ""$(e $printerSN)"",
        ""Salud"": { ""Uptime_Dias"": 0 }
    }"

    $servidor = "__INVENTARIO_SERVER_URL__/submit_inventory?api_key=__API_KEY__"
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("Content-Type", "application/json; charset=utf-8")
    $wc.Encoding = [System.Text.Encoding]::UTF8
    [void]$wc.UploadString($servidor, "POST", $json)
    
    Write-Log "Inventario SINCRONIZADO enviado exitosamente."
} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
}
}
