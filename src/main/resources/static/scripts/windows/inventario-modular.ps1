param(
    [Alias("Servidor", "Server", "Url", "Host", "server_url", "servidor_url")]
    [string]$ServerUrl = "http://localhost:8081/api/v1/equipos/inventario",
    [string]$Token = $env:INVENTARIO_REPORT_TOKEN,
    [string]$Fuero = $env:INVENTARIO_FUERO,
    [string]$BackupDirectory = "$env:ProgramData\InventarioModular",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Test-HasText {
    param($Value)
    if ($null -eq $Value) {
        return $false
    }
    return ([string]$Value).Trim().Length -gt 0
}

# Normalizar URL del servidor si el usuario paso solo la raiz o IP (ej: http://10.15.2.251:8081)
if (Test-HasText $ServerUrl) {
    $ServerUrl = $ServerUrl.Trim().TrimEnd('/')
    if (-not $ServerUrl.EndsWith("/api/v1/equipos/inventario", [System.StringComparison]::OrdinalIgnoreCase)) {
        $ServerUrl = "$ServerUrl/api/v1/equipos/inventario"
    }
}

if (-not (Test-HasText $Token)) {
    $Token = "dev-token-123456"
}

# Escapado minimo para armar JSON compatible con PowerShell viejo y moderno.
function ConvertTo-JsonString {
    param($Value)
    if ($null -eq $Value) {
        return ""
    }
    $Text = [string]$Value
    $Text = $Text.Replace("\", "\\")
    $Text = $Text.Replace('"', '\"')
    $Text = $Text -replace "`r", " "
    $Text = $Text -replace "`n", " "
    return $Text.Trim()
}

# Usa CIM en PowerShell moderno y WMI en equipos antiguos.
function Get-InventoryClass {
    param(
        [string]$ClassName,
        [string]$Filter = ""
    )
    if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) {
        if (-not (Test-HasText $Filter)) {
            return Get-CimInstance -ClassName $ClassName
        }
        return Get-CimInstance -ClassName $ClassName -Filter $Filter
    }
    if (-not (Test-HasText $Filter)) {
        return Get-WmiObject -Class $ClassName
    }
    return Get-WmiObject -Class $ClassName -Filter $Filter
}

function Get-FirstIPv4 {
    try {
        $Adapters = Get-InventoryClass -ClassName "Win32_NetworkAdapterConfiguration" -Filter "IPEnabled = True"
        foreach ($Adapter in $Adapters) {
            foreach ($Address in $Adapter.IPAddress) {
                if ($Address -match "^\d{1,3}(\.\d{1,3}){3}$" -and
                    -not $Address.StartsWith("127.") -and
                    -not $Address.StartsWith("169.254.")) {
                    return $Address
                }
            }
        }
    }
    catch {
        return ""
    }
    return ""
}

function Get-PrinterName {
    try {
        $DefaultPrinter = Get-InventoryClass -ClassName "Win32_Printer" | Where-Object { $_.Default -eq $true } | Select-Object -First 1
        if ($DefaultPrinter -and $DefaultPrinter.Name) {
            return $DefaultPrinter.Name
        }
        $Printer = Get-InventoryClass -ClassName "Win32_Printer" | Where-Object { $_.Name -notmatch "PDF|XPS|OneNote|Fax" } | Select-Object -First 1
        if ($Printer -and $Printer.Name) {
            return $Printer.Name
        }
    }
    catch {
        return ""
    }
    return ""
}

function Get-RamDetails {
    try {
        $Memories = Get-InventoryClass -ClassName "Win32_PhysicalMemory"
        $TypeMap = @{
            20 = "DDR"
            21 = "DDR2"
            24 = "DDR3"
            26 = "DDR4"
            34 = "DDR5"
        }
        $Details = @()
        $Serials = @()
        foreach ($Memory in $Memories) {
            $CapacityGb = 0
            if ($Memory.Capacity) {
                $CapacityGb = [Math]::Round($Memory.Capacity / 1GB, 0)
            }
            $TypeCode = 0
            if ($Memory.SMBIOSMemoryType) {
                $TypeCode = [int]$Memory.SMBIOSMemoryType
            }
            elseif ($Memory.MemoryType) {
                $TypeCode = [int]$Memory.MemoryType
            }
            $TypeName = ""
            if ($TypeMap.ContainsKey($TypeCode)) {
                $TypeName = $TypeMap[$TypeCode]
            }
            $Speed = ""
            if ($Memory.Speed) {
                $Speed = "$($Memory.Speed)MHz"
            }
            $Part = @()
            if ($CapacityGb -gt 0) { $Part += "$($CapacityGb)GB" }
            if (Test-HasText $TypeName) { $Part += $TypeName }
            if (Test-HasText $Speed) { $Part += $Speed }
            if ($Part.Count -gt 0) { $Details += [string]::Join(" ", $Part) }

            $Serial = ([string]$Memory.SerialNumber).Trim()
            if ((Test-HasText $Serial) -and $Serial -notmatch "^(0+|None|To be filled by O\.E\.M\.)$") {
                $Serials += $Serial
            }
        }
        return @{
            Details = [string]::Join(" | ", $Details)
            Serials = [string]::Join(" | ", $Serials)
        }
    }
    catch {
        return @{ Details = ""; Serials = "" }
    }
}

function Get-DiskDetails {
    try {
        $Disks = Get-InventoryClass -ClassName "Win32_DiskDrive"
        $Models = @()
        $Serials = @()
        foreach ($Disk in $Disks) {
            $Model = ([string]$Disk.Model).Trim()
            if (Test-HasText $Model) {
                $Models += $Model
            }
            $Serial = ([string]$Disk.SerialNumber).Trim()
            if ((Test-HasText $Serial) -and $Serial -notmatch "^(0+|None|To be filled by O\.E\.M\.)$") {
                $Serials += $Serial
            }
        }
        return @{
            Models = [string]::Join(" | ", $Models)
            Serials = [string]::Join(" | ", $Serials)
        }
    }
    catch {
        return @{ Models = ""; Serials = "" }
    }
}

function Get-MotherboardDetails {
    try {
        $Board = Get-InventoryClass -ClassName "Win32_BaseBoard" | Select-Object -First 1
        if (-not $Board) {
            return @{ Model = ""; Serial = "" }
        }
        $Model = ([string]"$($Board.Manufacturer) $($Board.Product)").Trim()
        $Serial = ([string]$Board.SerialNumber).Trim()
        return @{ Model = $Model; Serial = $Serial }
    }
    catch {
        return @{ Model = ""; Serial = "" }
    }
}

function Get-MonitorDetails {
    try {
        if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) {
            $MonitorItems = Get-CimInstance -Namespace root\WMI -ClassName WmiMonitorID -ErrorAction Stop
        }
        else {
            $MonitorItems = Get-WmiObject -Namespace root\WMI -Class WmiMonitorID -ErrorAction Stop
        }
        $Monitors = @()
        foreach ($Monitor in $MonitorItems) {
            $Manufacturer = -join ($Monitor.ManufacturerName | Where-Object { $_ -ne 0 } | ForEach-Object { [char]$_ })
            $Name = -join ($Monitor.UserFriendlyName | Where-Object { $_ -ne 0 } | ForEach-Object { [char]$_ })
            $Serial = -join ($Monitor.SerialNumberID | Where-Object { $_ -ne 0 } | ForEach-Object { [char]$_ })
            $Text = ([string]"$Manufacturer $Name $Serial").Trim()
            if (Test-HasText $Text) {
                $Monitors += $Text
            }
        }
        return [string]::Join(" | ", $Monitors)
    }
    catch {
        try {
            $MonitorItems = Get-InventoryClass -ClassName "Win32_DesktopMonitor"
            $Names = @()
            foreach ($Monitor in $MonitorItems) {
                if (Test-HasText $Monitor.Name) {
                    $Names += $Monitor.Name
                }
            }
            return [string]::Join(" | ", $Names)
        }
        catch {
            return ""
        }
    }
}

function Get-PeripheralName {
    param([string]$ClassName)
    try {
        $Device = Get-InventoryClass -ClassName $ClassName | Select-Object -First 1
        if ($Device -and $Device.Name) {
            return $Device.Name
        }
    }
    catch {
        return ""
    }
    return ""
}

function Save-InventoryBackup {
    param(
        [string]$Json,
        [string]$ComputerName
    )
    if (-not (Test-Path $BackupDirectory)) {
        New-Item -ItemType Directory -Path $BackupDirectory | Out-Null
    }
    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $Path = Join-Path $BackupDirectory "inventario-$ComputerName-$Timestamp.json"
    [System.IO.File]::WriteAllText($Path, $Json, [System.Text.Encoding]::UTF8)
    return $Path
}

function Send-InventoryJson {
    param(
        [string]$Json
    )
    $Client = New-Object System.Net.WebClient
    $Client.Headers.Add("Content-Type", "application/json; charset=utf-8")
    $Client.Headers.Add("Authorization", "Bearer $Token")
    $Client.Encoding = [System.Text.Encoding]::UTF8
    return $Client.UploadString($ServerUrl, "POST", $Json)
}

function Send-PendingBackups {
    if (-not (Test-Path $BackupDirectory)) {
        return
    }
    $PendingFiles = Get-ChildItem -Path $BackupDirectory -Filter "inventario-*.json" -ErrorAction SilentlyContinue |
        Where-Object { -not $_.PSIsContainer } |
        Sort-Object Name
    if ($null -eq $PendingFiles) {
        return
    }
    $SentDirectory = Join-Path $BackupDirectory "enviados"
    foreach ($PendingFile in $PendingFiles) {
        try {
            $PendingJson = [System.IO.File]::ReadAllText($PendingFile.FullName, [System.Text.Encoding]::UTF8)
            [void](Send-InventoryJson -Json $PendingJson)
            if (-not (Test-Path $SentDirectory)) {
                New-Item -ItemType Directory -Path $SentDirectory | Out-Null
            }
            $SentPath = Join-Path $SentDirectory $PendingFile.Name
            if (Test-Path $SentPath) {
                $SentPath = Join-Path $SentDirectory ("reenviado-" + (Get-Date -Format "yyyyMMdd-HHmmss") + "-" + $PendingFile.Name)
            }
            Move-Item -Path $PendingFile.FullName -Destination $SentPath
            Write-Host "Reporte pendiente reenviado: $($PendingFile.Name)" -ForegroundColor Green
        }
        catch {
            Write-Host "Queda pendiente $($PendingFile.Name): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

$ComputerSystem = Get-InventoryClass -ClassName "Win32_ComputerSystem"
$OperatingSystem = Get-InventoryClass -ClassName "Win32_OperatingSystem"
$Processor = Get-InventoryClass -ClassName "Win32_Processor" | Select-Object -First 1

$ComputerName = $env:COMPUTERNAME
$CurrentUser = $env:USERNAME
$IpAddress = Get-FirstIPv4
$RamMb = 0
if ($ComputerSystem.TotalPhysicalMemory) {
    $RamMb = [int][Math]::Round($ComputerSystem.TotalPhysicalMemory / 1MB)
}
$RamDetails = Get-RamDetails
$DiskDetails = Get-DiskDetails
$MotherboardDetails = Get-MotherboardDetails
$Monitors = Get-MonitorDetails
$Keyboard = Get-PeripheralName -ClassName "Win32_Keyboard"
$Mouse = Get-PeripheralName -ClassName "Win32_PointingDevice"

$Json = "{"
$Json += '"nombre":"' + (ConvertTo-JsonString $ComputerName) + '",'
$Json += '"ultimoUsuario":"' + (ConvertTo-JsonString $CurrentUser) + '",'
$Json += '"fuero":"' + (ConvertTo-JsonString $Fuero) + '",'
$Json += '"ip":"' + (ConvertTo-JsonString $IpAddress) + '",'
$Json += '"sistemaOperativo":"' + (ConvertTo-JsonString $OperatingSystem.Caption) + '",'
$Json += '"procesador":"' + (ConvertTo-JsonString $Processor.Name) + '",'
$Json += '"ramMb":' + $RamMb + ','
$Json += '"ramDetalles":"' + (ConvertTo-JsonString $RamDetails.Details) + '",'
$Json += '"ramSeriales":"' + (ConvertTo-JsonString $RamDetails.Serials) + '",'
$Json += '"discosModelos":"' + (ConvertTo-JsonString $DiskDetails.Models) + '",'
$Json += '"discosSeriales":"' + (ConvertTo-JsonString $DiskDetails.Serials) + '",'
$Json += '"motherboardModelo":"' + (ConvertTo-JsonString $MotherboardDetails.Model) + '",'
$Json += '"motherboardSerial":"' + (ConvertTo-JsonString $MotherboardDetails.Serial) + '",'
$Json += '"monitores":"' + (ConvertTo-JsonString $Monitors) + '",'
$Json += '"teclado":"' + (ConvertTo-JsonString $Keyboard) + '",'
$Json += '"mouse":"' + (ConvertTo-JsonString $Mouse) + '",'
$Json += '"impresora":"' + (ConvertTo-JsonString (Get-PrinterName)) + '",'
$Json += '"activo":true'
$Json += "}"

if ($DryRun) {
    Write-Host $Json
    exit 0
}

Write-Host "Enviando inventario de $ComputerName a $ServerUrl ..."

try {
    Send-PendingBackups
    $Response = Send-InventoryJson -Json $Json
    Write-Host "Inventario enviado correctamente." -ForegroundColor Green
    Write-Host $Response
}
catch {
    Write-Host "No se pudo enviar el inventario: $($_.Exception.Message)" -ForegroundColor Yellow
    $BackupPath = Save-InventoryBackup -Json $Json -ComputerName $ComputerName
    Write-Host "Se guardo una copia local en: $BackupPath" -ForegroundColor Yellow
    exit 1
}
