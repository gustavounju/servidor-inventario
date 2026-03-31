& {
# Inventario GOLD - Cliente
# Compatible con Windows 7 (PowerShell 2.0) y Windows 10/11
# V2.0 - Corrección para "ConvertTo-Json" y "Invoke-RestMethod"
# -----------------------------------------------------------
# CONFIGURACIÓN DE LOGGING (DEBUGGING)
# -----------------------------------------------------------
$ErrorActionPreference = "Continue"
$script:errorOccurred = $false
# CONFIGURACIÓN PREVIA (SEGURIDAD Y RED)
# -----------------------------------------------------------
# FIX: ACTIVAR TLS 1.2 POR REGISTRO (CRÍTICO PARA WINDOWS 7)
try {
    # .NET 4.x
    $path4 = 'HKLM:\SOFTWARE\Microsoft\.NETFramework\v4.0.30319'
    if (Test-Path $path4) {
        New-ItemProperty -Path $path4 -Name 'SchUseStrongCrypto' -Value '1' -PropertyType 'DWord' -Force -ErrorAction SilentlyContinue | Out-Null
        New-ItemProperty -Path $path4 -Name 'SystemDefaultTlsVersions' -Value '1' -PropertyType 'DWord' -Force -ErrorAction SilentlyContinue | Out-Null
    }
    # .NET 2.0/3.5 (Default en Win7)
    $path2 = 'HKLM:\SOFTWARE\Microsoft\.NETFramework\v2.0.50727'
    if (Test-Path $path2) {
        New-ItemProperty -Path $path2 -Name 'SchUseStrongCrypto' -Value '1' -PropertyType 'DWord' -Force -ErrorAction SilentlyContinue | Out-Null
        New-ItemProperty -Path $path2 -Name 'SystemDefaultTlsVersions' -Value '1' -PropertyType 'DWord' -Force -ErrorAction SilentlyContinue | Out-Null
    }
}
catch {
    # Puede fallar si no hay permisos de admin, pero intentamos
}
# Forzar TLS 1.2 (Protocolo 3072) en la sesión actual
try {
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
}
catch {
    try {
        [System.Net.ServicePointManager]::SecurityProtocol = 3072
    }
    catch {
        # Ignorar si falla por completo
    }
}
# -----------------------------------------------------------
# BYPASS DE VALIDACIÓN SSL (Para certificados autofirmados)
# -----------------------------------------------------------
try {
    # Crear una clase que acepta todos los certificados (Formato de 1 línea para evitar problemas de copy-paste en PS 2.0)
    add-type "using System.Net; using System.Security.Cryptography.X509Certificates; public class TrustAllCertsPolicy : ICertificatePolicy { public bool CheckValidationResult(ServicePoint srvPoint, X509Certificate certificate, WebRequest request, int certificateProblem) { return true; } }"
    [System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
}
catch {
    # Si falla (ej: ya existe la clase), continuar
}
# JSON polyfill function removed to maximize PS 2.0 copy-paste compatibility
# -----------------------------------------------------------
# FUNCIÓN: Obtener Conexiones de Red (Snapshot)
# -----------------------------------------------------------
function Get-ActiveConnections {
    $conns = @()
    # Usamos netstat -ano para obtener PID sin requerir elevación para -b (que a veces falla)
    # Filtramos por ESTABLISHED o SYN_SENT (intentos de conexión)
    $netstatOutput = netstat -ano | Select-String "ESTABLISHED|SYN_SENT"
    foreach ($line in $netstatOutput) {
        # Parsear línea: Proto Local Foreign State PID
        # Ej: TCP 192.168.1.5:54321 1.2.3.4:443 ESTABLISHED 1234
        # Split por espacios múltiples (Compatible con PS 2.0 usando regex)
        $parts = $line.ToString().Trim() -split "\s+"
        if ($parts.Count -ge 5) {
            $proto = $parts[0]
            $local = $parts[1]
            $remote = $parts[2]
            $state = $parts[3]
            # Corregir indice PID si hay columnas extrañas, pero en -ano suele ser el ultimo
            $pidVal = $parts[$parts.Count - 1]
            # Filtrar Loopback y Localhost explícito
            if ($remote -like "127.0.0.1*" -or $remote -like "[::1]*" -or $remote -like "0.0.0.0*") { continue }
            # Obtener Nombre del Proceso
            $procName = "Desconocido ($pidVal)"
            try {
                $p = Get-Process -Id $pidVal -ErrorAction Stop
                if ($p) { $procName = $p.ProcessName }
            }
            catch {}
            # Crear objeto simple
            $connObj = @{
                "Proto"   = $proto
                "Local"   = $local
                "Remote"  = $remote
                "State"   = $state
                "PID"     = $pidVal
                "Process" = $procName
            }
            $conns += $connObj
        }
    }
    return $conns
}
# -----------------------------------------------------------
# FUNCIÓN: Obtener Salud del Sistema (WMI / Eventos)
# -----------------------------------------------------------
function Get-ComputerHealth {
    $health = @{}
    # 1. Estado SMART de Discos
    $diskStatus = @()
    try {
        $disks = Get-WmiObject -Class Win32_DiskDrive
        if ($disks) {
            foreach ($d in $disks) {
                # Status: "OK", "Pred Fail", "Error", etc.
                $diskStatus += @{ "Model" = $d.Model; "Status" = $d.Status; "DeviceID" = $d.DeviceID }
            }
        }
    }
    catch {}
    $health.Add("Discos_SMART", $diskStatus)
    # 2. Espacio en Disco (Crítico < 5GB)
    $diskSpace = @()
    try {
        $vols = Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3" # 3 = Local Disk
        if ($vols) {
            foreach ($v in $vols) {
                if ($v.Size -gt 0) {
                    $gbFree = [math]::Round($v.FreeSpace / 1GB, 2)
                    $gbTotal = [math]::Round($v.Size / 1GB, 2)
                    $pctFree = [math]::Round(($v.FreeSpace / $v.Size) * 100, 1)
                    $diskSpace += @{ "Letter" = $v.DeviceID; "FreeGB" = $gbFree; "TotalGB" = $gbTotal; "PctFree" = $pctFree }
                }
            }
        }
    }
    catch {}
    $health.Add("Discos_Espacio", $diskSpace)
    # 3. Uptime (Días sin reiniciar)
    $uptimeDays = 0
    try {
        $os = Get-WmiObject -Class Win32_OperatingSystem
        # ConvertToDateTime funciona en PS 2.0+
        $lastBoot = $os.ConvertToDateTime($os.LastBootUpTime)
        $uptime = (Get-Date) - $lastBoot
        $uptimeDays = [math]::Round($uptime.TotalDays, 1)
    }
    catch {}
    $health.Add("Uptime_Dias", $uptimeDays)
    # 4. Errores Críticos Recientes (Últimas 24hs) - System y Application
    $recentErrors = @()
    try {
        # Limitamos a 5 para no saturar JSON
        $yesterday = (Get-Date).AddDays(-1)
        $evts = Get-EventLog -LogName System -EntryType Error -After $yesterday -Newest 5 -ErrorAction SilentlyContinue
        if ($evts) {
            foreach ($e in $evts) {
                $recentErrors += @{ "Log" = "System"; "Source" = $e.Source; "Msg" = $e.Message.Trim().Substring(0, [math]::Min($e.Message.Length, 100)) }
            }
        }
    }
    catch {}
    $health.Add("Eventos_Criticos", $recentErrors)
    return $health
}
# -----------------------------------------------------------
# FUNCIÓN: Obtener Seguridad Extra (Antivirus y Startup)
# -----------------------------------------------------------
function Get-SecurityExtra {
    $sec = @{}
    
    # 1. Antivirus (WMI SecurityCenter2)
    $avName = "No Detectado"
    try {
        $avs = Get-WmiObject -Namespace root\SecurityCenter2 -Class AntiVirusProduct -ErrorAction SilentlyContinue
        if ($avs) {
            $names = @()
            if ($avs -is [array]) {
                foreach ($a in $avs) { $names += $a.displayName }
            }
            else {
                $names += $avs.displayName
            }
            $avName = [string]::Join(" / ", $names)
        }
    }
    catch {}
    $sec.Add("Antivirus", $avName)
    
    # 2. Startup Programs (Registry HKLM & HKCU)
    $startupArr = @()
    try {
        $paths = @("HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
        foreach ($p in $paths) {
            if (Test-Path $p) {
                $items = Get-ItemProperty $p -ErrorAction SilentlyContinue
                if ($items) {
                    foreach ($prop in $items.psobject.properties) {
                        $name = $prop.Name
                        if ($name -notmatch "^PS[A-Z]") {
                            $val = $prop.Value
                            if ($val -is [string]) {
                                $startupArr += @{ "Name" = $name; "Command" = $val }
                            }
                        }
                    }
                }
            }
        }
    }
    catch {}
    $sec.Add("Startup", $startupArr)
    
    return $sec
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
        # Obtener todas las impresoras
        $allPrinters = Get-WmiObject -Class Win32_Printer
        
        # 1. Buscar la impresora PREDETERMINADA
        $virtualKeywords = "PDF|XPS|OneNote|Fax|Send To|Microsoft Print|Writer"
        $bestPrinter = $allPrinters | Where-Object { $_.Default -eq $true } | Select-Object -First 1
        
        # 2. Si la default es virtual o nula, intentar buscar la primera que NO sea virtual
        if (-not $bestPrinter -or $bestPrinter.Name -match $virtualKeywords) {
            $bestPrinter = $allPrinters | Where-Object { $_.Name -notmatch $virtualKeywords } | Select-Object -First 1
        }

        # 3. Datos de la impresora
        $printerSN = "N/A"
        if ($bestPrinter) {
            $printerModel = $bestPrinter.Name
            $printerPort = $bestPrinter.PortName

            # INTENTAR OBTENER SERIAL FÍSICO (USB / PnP)
            try {
                # 1. Búsqueda directa por PnPEntity con filtrado por Service:usbprint (más certero)
                $pnpDevices = Get-WmiObject Win32_PnPEntity -ErrorAction SilentlyContinue | Where-Object { $_.Service -eq "usbprint" -or $_.Name -like "*$printerModel*" }
                
                foreach ($pnp in $pnpDevices) {
                    # Si el nombre del dispositivo coincide al menos parcialmente con el modelo reportado
                    if ($pnp.Name -match [regex]::Escape($printerModel) -or $printerModel -match [regex]::Escape($pnp.Name)) {
                        # El DeviceID suele ser: USBPRINT\MODEL\SERIAL
                        if ($pnp.DeviceID -match "\\([^\\]+)$") {
                            $potentialSN = $matches[1] -replace "_\d+$", "" # Quitar sufijos de Windows si existen (_0, _1)
                            
                            # Validar que no sea un ID genérico o GUID
                            $isGuid = $potentialSN -match "^\{[A-F0-9-]+\}$" -or ($potentialSN -split "-").Count -gt 3
                            if ($potentialSN -notmatch "^(USB|LPT|COM)[0-9]+$" -and -not $isGuid -and $potentialSN.Length -gt 4) {
                                $printerSN = $potentialSN
                                break
                            }
                        }
                    }
                }

                # 2. Fallback por Registro (Enum\USBPRINT) si falla el WMI
                if ($printerSN -eq "N/A") {
                    $usbPrintPath = "HKLM:\SYSTEM\CurrentControlSet\Enum\USBPRINT"
                    if (Test-Path $usbPrintPath) {
                        $models = Get-ChildItem $usbPrintPath -ErrorAction SilentlyContinue
                        foreach ($m in $models) {
                            # Limpiamos nombres para comparar (quitar underscores, espacios)
                            $cleanM = $m.PSChildName -replace "[_\s]", ""
                            $cleanP = $printerModel -replace "[_\s]", ""
                            if ($cleanP -match $cleanM -or $cleanM -match $cleanP) {
                                $serialKeys = Get-ChildItem $m.PSPath -ErrorAction SilentlyContinue
                                if ($serialKeys) {
                                    $potentialSN = $serialKeys[0].PSChildName -replace "(_|\&).*$", ""
                                    if ($potentialSN.Length -gt 5 -and $potentialSN -notmatch "^[A-F0-9]{8}-") {
                                        $printerSN = $potentialSN
                                        break
                                    }
                                }
                            }
                        }
                    }
                }

                # 3. Fallback por PrinterDriverData (Software\Microsoft\Windows NT\CurrentVersion\Print\Printers)
                if ($printerSN -eq "N/A") {
                    $printerRegistryPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Print\Printers\$printerModel\PrinterDriverData"
                    if (Test-Path $printerRegistryPath) {
                        $potentialSN = Get-ItemProperty -Path $printerRegistryPath -Name "SerialNumber" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty SerialNumber -ErrorAction SilentlyContinue
                        if ($null -ne $potentialSN -and $potentialSN.Length -gt 4) {
                            $printerSN = $potentialSN
                        }
                    }
                }
            } catch {}
            # Limpiar prefijos/sufijos internos de Windows (Ej: IP_10.15.2.50_1 -> 10.15.2.50)
            $printerPort = $printerPort -replace "^IP_", "" -replace "_[0-9]+$", ""
            
            # Soporte para puertos WSD (Web Services for Devices)
            # Intenta extraer la IP real desde el registro si el puerto es un GUID de WSD
            if ($printerPort -like "WSD-*") {
                try {
                    $regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Print\Monitors\WSD Port\Ports\$($bestPrinter.PortName)"
                    if (Test-Path $regPath) {
                        # 1. Intentar obtener el UUID de la impresora vinculado a este puerto
                        $pUuid = (Get-ItemProperty $regPath)."Printer UUID"
                        if ($pUuid) {
                            # 2. Buscar en la caché de descubrimiento de Windows (DAFWSDProvider)
                            $dafPath = "HKLM:\SYSTEM\CurrentControlSet\Enum\SWD\DAFWSDProvider\urn:uuid:$pUuid"
                            $locInfo = ""
                            
                            # Intentar en la raíz del dispositivo o en la subclave PrinterService
                            if (Test-Path $dafPath) {
                                $locInfo = (Get-ItemProperty $dafPath -ErrorAction SilentlyContinue).LocationInformation
                                if (-not $locInfo -and (Test-Path "$dafPath\PrinterService")) {
                                    $locInfo = (Get-ItemProperty "$dafPath\PrinterService" -ErrorAction SilentlyContinue).LocationInformation
                                }
                            }

                            # Si encontramos una URL, extraer la IP
                            if ($locInfo -and $locInfo -match "https?://([^:/]+)") {
                                $printerPort = $matches[1]
                            }
                        }
                    }
                }
                catch {
                    # Si falla cualquier paso, se mantiene el GUID original (WSD-...)
                }
            }
            
            # Etiquetar tipo
            # 1. Definitivamente RED (Conexión a servidor de impresión o share)
            if ($bestPrinter.Network -eq $true -or $printerPort -like "\\*") {
                $printerPort += " (Red)"
            }
            # 2. Puertos LOCALES conocidos (Físicos y Virtuales de Sisema)
            elseif ($printerPort -like "USB*" -or $printerPort -like "DOT4*" -or $printerPort -like "LPT*" -or $printerPort -like "COM*" -or $printerPort -like "FILE:" -or $printerPort -like "NUL:" -or $printerPort -like "PORTPROMPT:" -or $printerPort -like "*PDF*" -or $printerPort -like "*XPS*") {
                $printerPort += " (Local)"
                
                # Verificación PnP para cables USB/DOT4
                if ($printerPort -like "USB*" -or $printerPort -like "DOT4*") {
                    $cleanName = $bestPrinter.Name -replace "[\\]", "\\"
                    try {
                        $pnp = Get-WmiObject Win32_PnPEntity -ErrorAction SilentlyContinue | Where-Object { $_.Name -match [regex]::Escape($cleanName) -or $_.Description -match [regex]::Escape($cleanName) }
                        if (-not $pnp -or $pnp.Status -ne "OK") {
                            $printerPort += " [DESCONECTADA]"
                        }
                    }
                    catch {}
                }
            }
            # 3. TODO LO DEMÁS se asume RED (TCP/IP directo, DNS, Ricoh LAN, WSD, etc)
            else {
                $printerPort += " (Red)"
            }
        }
    }
    catch {
        Write-Host "Error detectando impresora: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    # 7) Monitores (WmiMonitorID a veces falla en Win7 si no hay permisos, try-catch)
    $monitorsStr = "N/A"
    try {
        $monItems = Get-WmiObject -Namespace root\WMI -Class WmiMonitorID -ErrorAction SilentlyContinue
        if ($monItems) {
            $mList = @()
            foreach ($m in $monItems) {
                # Convertir array de ints a string chars manual
                $mn = ""
                if ($m -and $m.ManufacturerName) {
                    foreach ($c in $m.ManufacturerName) { if ($c -ne 0) { $mn += [char]$c } }
                }
                $mList += $mn
            }
            if ($mList.Count -gt 0) {
                $monitorsStr = [string]::Join(" | ", $mList)
            }
        }
    }
    catch {}
    
    # Fallback para monitores en Windows 10/11 si WmiMonitorID falla por falta de permisos
    if ($monitorsStr -eq "N/A" -or $monitorsStr -eq "") {
        try {
            $monItemsV2 = Get-WmiObject -Class Win32_DesktopMonitor -ErrorAction SilentlyContinue
            if ($monItemsV2) {
                $mListV2 = @()
                foreach ($m in $monItemsV2) {
                    if ($m.MonitorType -and $m.MonitorType -ne "Monitor PnP genérico") {
                        $mListV2 += $m.MonitorType
                    }
                    elseif ($m.Description) {
                        $mListV2 += $m.Description
                    }
                    else {
                        $mListV2 += "Monitor Reconocido"
                    }
                }
                if ($mListV2.Count -gt 0) {
                    $monitorsStr = [string]::Join(" | ", $mListV2)
                }
            }
        }
        catch {}
    }
    # 8) Seguridad (Conexiones Activas)
    $activeConns = @()
    try {
        $activeConns = Get-ActiveConnections
    }
    catch {}
    # 9) Salud y Diagnóstico
    $healthData = @{}
    try {
        $healthData = Get-ComputerHealth
    }
    catch {}
    # 10) Seguridad Extra (Antivirus, Startup)
    $secExtra = @{}
    try {
        $secExtra = Get-SecurityExtra
    }
    catch {}
    # -----------------------------------------------------------
    # CONSTRUCCIÓN DEL PAYLOAD (JSON MANUAL PARA EVITAR ERRORES PS2.0)
    # -----------------------------------------------------------
    # Para máxima compatibilidad al copiar/pegar en PowerShell 2.0, evitamos
    # usar comillas invertidas (backticks) complejas.
    # Armamos un JSON lineal básico usando comillas simples externas o escapando con ""
    # helper rapidísimo para escapar strings en PS2.0 y manejar Nulls
    function e($s) { 
        if ($null -eq $s) { return "" }
        # Escapado JSON básico para PS 2.0 (Backslash y Comillas)
        $val = [string]$s
        $val = $val -replace "\\", "\\\\"
        $val = $val -replace "`"", "\`""
        $val = $val -replace "`r", ""
        $val = $val -replace "`n", ""
        return $val
    }
    $jsonObj = "{"
    $jsonObj += """PC_Nombre"": ""$(e $pcNombre)"","
    $jsonObj += """Usuario_Actual"": ""$(e $usuarioActual)"","
    $jsonObj += """Fecha_Reporte"": ""$fechaReporte"","
    $jsonObj += """Sistema"": {"
    $jsonObj += """OsName"": ""$(e $os.Caption)"","
    $jsonObj += """Procesador"": ""$(e $cpu.Name)"","
    $jsonObj += """RAM (GB)"": $ramGB"
    $jsonObj += "},"
    $jsonObj += """Red"": [{""IPAddress"": ""$ipAddress""}],"
    $jsonObj += """RAM_Detalles"": ""$(e $ramDetalles)"","
    $jsonObj += """Disk_Models"": ""$(e $diskModelsStr)"","
    $jsonObj += """Disk_Speeds_RPM"": ""$(e $diskSpeedsStr)"","
    $jsonObj += """Motherboard_Model"": ""$(e $motherboardModel)"","
    $jsonObj += """Printer_Model"": ""$(e $printerModel)"","
    $jsonObj += """Printer_Port"": ""$(e $printerPort)"","
    $jsonObj += """Printer_SN"": ""$(e $printerSN)"","
    $jsonObj += """Monitors"": ""$(e $monitorsStr)"","
    # Armamos array Conexiones
    $jsonObj += """Conexiones"": ["
    $connArr = @()
    foreach ($c in $activeConns) {
        $connArr += "{""Proto"":""$(e $c.Proto)"",""Local"":""$(e $c.Local)"",""Remote"":""$(e $c.Remote)"",""State"":""$(e $c.State)"",""PID"":""$(e $c.PID)"",""Process"":""$(e $c.Process)""}"
    }
    $jsonObj += [string]::Join(",", $connArr)
    $jsonObj += "],"
    # Armamos objeto Salud
    $jsonObj += """Salud"": {"
    $jsonObj += """Uptime_Dias"": $($healthData.Uptime_Dias),"
    $jsonObj += """Discos_SMART"": ["
    $smartArr = @()
    if ($null -ne $healthData.Discos_SMART) {
        foreach ($d in $healthData.Discos_SMART) {
            $smartArr += "{""Model"":""$(e $d.Model)"",""Status"":""$(e $d.Status)"",""DeviceID"":""$(e $d.DeviceID)""}"
        }
    }
    $jsonObj += [string]::Join(",", $smartArr)
    $jsonObj += "],"
    $jsonObj += """Discos_Espacio"": ["
    $spcArr = @()
    if ($null -ne $healthData.Discos_Espacio) {
        foreach ($v in $healthData.Discos_Espacio) {
            $spcArr += "{""Letter"":""$(e $v.Letter)"",""FreeGB"":$($v.FreeGB),""TotalGB"":$($v.TotalGB),""PctFree"":$($v.PctFree)}"
        }
    }
    $jsonObj += [string]::Join(",", $spcArr)
    $jsonObj += "],"
    $jsonObj += """Eventos_Criticos"": ["
    $evtArr = @()
    if ($null -ne $healthData.Eventos_Criticos) {
        foreach ($e in $healthData.Eventos_Criticos) {
            $evtArr += "{""Log"":""$(e $e.Log)"",""Source"":""$(e $e.Source)"",""Msg"":""$(e $e.Msg)""}"
        }
    }
    $jsonObj += [string]::Join(",", $evtArr)
    $jsonObj += "]"
    $jsonObj += "},"
    $jsonObj += """Seguridad_Extra"": {"
    $jsonObj += """Antivirus"": ""$(e $secExtra.Antivirus)"","
    $jsonObj += """Startup"": ["
    $strpArr = @()
    if ($null -ne $secExtra.Startup) {
        foreach ($s in $secExtra.Startup) {
            # Fix backslash escaping for valid JSON
            $pName = ($s.Name) -replace "[\\]", "\\\\" -replace "`"", "\`""
            $pCmd = ($s.Command) -replace "[\\]", "\\\\" -replace "`"", "\`""
            $strpArr += "{""Name"":""$pName"",""Command"":""$pCmd""}"
        }
    }
    $jsonObj += [string]::Join(",", $strpArr)
    $jsonObj += "]"
    $jsonObj += "}"
    $jsonObj += "}"
    $json = $jsonObj -replace "`r", ""
    $json = $json -replace "`n", ""
    # -----------------------------------------------------------
    # ENVÍO AL SERVIDOR (WEBCLIENT PARA COMPATIBILIDAD)
    # -----------------------------------------------------------
    $servidor = "__INVENTARIO_SERVER_URL__/submit_inventory"
    Write-Host "Enviando a $servidor ..."
    try {
        # Usamos System.Net.WebClient porque Invoke-RestMethod no existe en PS 2.0
        $wc = New-Object System.Net.WebClient
        $wc.Headers.Add("Content-Type", "application/json; charset=utf-8")
        $wc.Encoding = [System.Text.Encoding]::UTF8
        [void]$wc.UploadString($servidor, "POST", $json)
        Write-Host "Inventario enviado EXITOSAMENTE (HTTPS)." -ForegroundColor Green
    }
    catch {
        Write-Host "Fallo HTTPS: $($_.Exception.Message). Intentando HTTP (Puerto 8080)..." -ForegroundColor Yellow
        # FALLBACK: Intentar HTTP en puerto 8080 (legacy/mobile)
        try {
            # Cambiar URL a HTTP y puerto 8080
            # Asumimos que la IP es la misma, solo cambia protocolo y puerto
            # $servidor = "https://10.15.2.251:5000/submit_inventory" -> "http://10.15.2.251:8080/submit_inventory"
            $servidorHttp = $servidor.Replace("https://", "http://").Replace(":5000", ":8080")
            $wc = New-Object System.Net.WebClient
            $wc.Headers.Add("Content-Type", "application/json; charset=utf-8")
            $wc.Encoding = [System.Text.Encoding]::UTF8
            [void]$wc.UploadString($servidorHttp, "POST", $json)
            Write-Host "Inventario enviado EXITOSAMENTE (HTTP)." -ForegroundColor Green
        }
        catch {
            $script:errorOccurred = $true
            Write-Host "ERROR FATAL: Falló tanto HTTPS como HTTP." -ForegroundColor Red
            Write-Host "HTTPS Error: $($_.Exception.Message)" -ForegroundColor Red
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
    }
    # -----------------------------------------------------------
    # FINALIZAR EJECUCIÓN
    # -----------------------------------------------------------
}
catch {
    $script:errorOccurred = $true
    Write-Host "ERROR CRITICO GLOBAL:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
}
# -----------------------------------------------------------
# FINALIZAR
# -----------------------------------------------------------
if ($script:errorOccurred) {
    Write-Host "---------------------------------------------------" -ForegroundColor Red
    Write-Host "Ocurrió un error general durante la recolección." -ForegroundColor Yellow
    Write-Host "---------------------------------------------------" -ForegroundColor Red
    Start-Sleep -Seconds 10
}
else {
    Stop-Process -Id $PID
}
}


