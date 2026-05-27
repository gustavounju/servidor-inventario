$printers = Get-WmiObject Win32_Printer
foreach ($p in $printers) {
    Write-Host "Nombre: $($p.Name)"
    Write-Host "Port: $($p.PortName)"
    Write-Host "PNP: $($p.PNPDeviceID)"
    Write-Host "---"
}
