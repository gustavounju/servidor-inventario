& {
# Inventario GOLD - Versión Silenciosa para GPO (SYSTEM)
# Optimizado para ejecución masiva sin ventanas ni interacción
# -----------------------------------------------------------

$ErrorActionPreference = "SilentlyContinue"
$logFile = "C:\Windows\Temp\inventario_gold.log"

function Write-Log {
    param($msg)
    "[" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "] $msg" | Out-File $logFile -Append
}

Write-Log "Iniciando recolección de datos..."

# -----------------------------------------------------------
# CONFIGURACIÓN DE SEGURIDAD (TLS 1.2 y Bypass SSL)
# -----------------------------------------------------------
try {
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    add-type "using System.Net; using System.Security.Cryptography.X509Certificates; public class TrustAllCertsPolicy : ICertificatePolicy { public bool CheckValidationResult(ServicePoint srvPoint, X509Certificate certificate, WebRequest request, int certificateProblem) { return true; } }"
    [System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
} catch {}

# -----------------------------------------------------------
# RECOLECCIÓN (Versión compacta para SYSTEM)
# -----------------------------------------------------------
try {
    # Datos básicos
    $os = Get-WmiObject Win32_OperatingSystem
    $cs = Get-WmiObject Win32_ComputerSystem
    $cpu = Get-WmiObject Win32_Processor | Select-Object -First 1
    
    # Red
    $netCfg = Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled = True" | Select-Object -First 1
    $ip = if ($netCfg.IPAddress -is [array]) { $netCfg.IPAddress[0] } else { $netCfg.IPAddress }
    
    # RAM
    $ramGB = if ($cs.TotalPhysicalMemory) { [math]::Round($cs.TotalPhysicalMemory / 1GB, 2) } else { 0 }
    
    # Impresoras
    $allPrinters = Get-WmiObject Win32_Printer
    $bestPrinter = $allPrinters | Where-Object { $_.Default -eq $true } | Select-Object -First 1
    if (-not $bestPrinter -or $bestPrinter.Name -match "PDF|XPS|OneNote|Fax") {
        $bestPrinter = $allPrinters | Where-Object { $_.Name -notmatch "PDF|XPS|OneNote|Fax" } | Select-Object -First 1
    }
    
    $printerSN = "N/A"
    if ($bestPrinter) {
        # Como corre como SYSTEM, intentamos leer el serial directamente del registro
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
    # CONSTRUCCIÓN DEL JSON (Estructura Minimalista)
    # -----------------------------------------------------------
    $json = "{
        ""PC_Nombre"": ""$env:COMPUTERNAME"",
        ""Usuario_Actual"": ""$env:USERNAME"",
        ""Fecha_Reporte"": ""$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"",
        ""Sistema"": {
            ""OsName"": ""$($os.Caption)"",
            ""Procesador"": ""$($cpu.Name)"",
            ""RAM (GB)"": $ramGB
        },
        ""Red"": [{""IPAddress"": ""$ip"", ""MACAddress"": ""$($netCfg.MACAddress)""}],
        ""Printer_Model"": ""$($bestPrinter.Name)"",
        ""Printer_Port"": ""$($bestPrinter.PortName)"",
        ""Printer_SN"": ""$printerSN"",
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
    
    Write-Log "Inventario enviado exitosamente a $servidor"
} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
}
}
