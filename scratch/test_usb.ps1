$usbPath = "HKLM:\SYSTEM\CurrentControlSet\Enum\USB"
$usbDevices = Get-ChildItem $usbPath -ErrorAction SilentlyContinue

foreach ($dev in $usbDevices) {
    $instances = Get-ChildItem $dev.PSPath -ErrorAction SilentlyContinue
    foreach ($inst in $instances) {
        $svc = Get-ItemProperty $inst.PSPath -Name "Service" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Service
        $class = Get-ItemProperty $inst.PSPath -Name "Class" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Class
        
        if ($svc -match "usbprint|dot4|bpusb" -or $class -match "Printer") {
            $serial = $inst.PSChildName
            Write-Host "Found USB Printer Device:"
            Write-Host "  Path: $($inst.PSPath)"
            Write-Host "  Service: $svc"
            Write-Host "  Class: $class"
            Write-Host "  Device SN: $serial"
        }
    }
}
