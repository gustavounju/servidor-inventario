import re

with open("inventario.ps1", "r", encoding="utf-8") as f:
    text = f.read()

# Refactorización del bloque de impresoras
# Encontrar bloque
block_start = text.find('    # 6) Impresora\n')
block_end = text.find('    # 7) Monitores')

printer_block = text[block_start:block_end]

# Quiero envolver la lógica en una función o loop, o mejor, simplemente la modifico:
new_block = """    # 6) Impresoras Multidetección
    $printerModel = "N/A"
    $printerPort = "N/A"
    $printerSN = "N/A"
    $detectedPrintersList = @()

    try {
        # Obtener todas las impresoras
        $allPrinters = Get-WmiObject -Class Win32_Printer
        $virtualKeywords = "PDF|XPS|OneNote|Fax|Send To|Microsoft Print|Writer|WebEx|Document"
        
        # Retrocompatibilidad: Identificar la principal como antes
        $primaryP = $allPrinters | Where-Object { $_.Default -eq $true } | Select-Object -First 1
        if (-not $primaryP -or $primaryP.Name -match $virtualKeywords) {
            $primaryP = $allPrinters | Where-Object { $_.Name -notmatch $virtualKeywords } | Select-Object -First 1
        }
        $primaryPName = if ($primaryP) { $primaryP.Name } else { "" }

        $realPrinters = $allPrinters | Where-Object { $_.Name -notmatch $virtualKeywords }
        
        foreach ($currentPrinter in $realPrinters) {
            $bestPrinter = $currentPrinter
            $printerModel = $bestPrinter.Name
            $printerPort = $bestPrinter.PortName
            $printerSN = "N/A"
            
            # INTENTAR OBTENER SERIAL FÍSICO (USB / PnP)
"""

# Extraer el interior de try { if ($bestPrinter) { ... } } }
inner_start = printer_block.find('            # INTENTAR OBTENER SERIAL FÍSICO (USB / PnP)')
inner_end = printer_block.find('    } catch {')

inner_logic = printer_block[inner_start:inner_end]

# Eliminar un nivel de indentación
# Ya que $bestPrinter ya no está dentro de if ($bestPrinter) { }, lo estaba antes
# Pero lo podemos dejar igual de indentado para no romper nada.

new_block += inner_logic

new_block += """
            $detectedPrintersList += @{
                "Model" = $printerModel
                "Port" = $printerPort
                "SN" = $printerSN
                "IsPrimary" = ($bestPrinter.Name -eq $primaryPName)
            }
            
            if ($bestPrinter.Name -eq $primaryPName) {
                # Guardamos copia local para la raiz del JSON
                $mainModel = $printerModel
                $mainPort = $printerPort
                $mainSN = $printerSN
            }
        }
        
        if ($detectedPrintersList.Count -gt 0) {
            # Restaurar var globales para compatibilidad 1 a 1 de la PC
            if ($mainModel) {
                $printerModel = $mainModel; $printerPort = $mainPort; $printerSN = $mainSN
            } else {
                $printerModel = $detectedPrintersList[0].Model
                $printerPort = $detectedPrintersList[0].Port
                $printerSN = $detectedPrintersList[0].SN
            }
        } else {
            $printerModel = "N/A"; $printerPort = "N/A"; $printerSN = "N/A"
        }
    } catch {
        Write-Host "Error detectando impresora: $($_.Exception.Message)" -ForegroundColor Yellow
    }
"""

text = text.replace(printer_block, new_block)

# Ahora hay que meter $detectedPrintersList en el JSON
json_block_start = text.find('$jsonObj += """Printer_SN"": ""$(e $printerSN)"","\n')
json_addition = """    $jsonObj += \"""Printers_Extra\"": [\"
    $peArr = @()
    if ($null -ne $detectedPrintersList) {
        foreach ($pe in $detectedPrintersList) {
            $peArr += \"{\""Model\"":\""$(e $pe.Model)\"\",\""Port\"":\""$(e $pe.Port)\"\",\""SN\"":\""$(e $pe.SN)\"\"}\"
        }
    }
    $jsonObj += [string]::Join(\",\", $peArr)
    $jsonObj += \"],\"
"""
text = text[:json_block_start + len('$jsonObj += """Printer_SN"": ""$(e $printerSN)"","\n')] + json_addition + text[json_block_start + len('$jsonObj += """Printer_SN"": ""$(e $printerSN)"","\n'):]

with open("inventario.ps1", "w", encoding="utf-8") as f:
    f.write(text)

print("Refactor PowerShell completado.")
