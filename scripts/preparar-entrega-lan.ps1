# Genera un kit transportable a partir de binarios ya probados y un commit limpio.
# No compila, no descarga dependencias y no copia secretos ni datos de la aplicacion.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $root
try {
    $branch = git branch --show-current
    if ($LASTEXITCODE -ne 0 -or $branch -ne 'primeros-pasos') { throw 'Se requiere la rama primeros-pasos.' }
    $dirty = git status --porcelain --untracked-files=normal
    if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Confirmar los cambios antes de generar el kit.' }
    $commit = git rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo resolver el commit.' }
    $files = [ordered]@{
        'target/inventario-modular-0.0.1-SNAPSHOT.jar' = 'inventario-modular.jar'
        'android/app/build/outputs/apk/debug/app-debug.apk' = 'tareas-lan-piloto.apk'
        'output/pdf/traspaso-tareas-lan.pdf' = 'traspaso-tareas-lan.pdf'
        'docs/inventario-modular/traspaso-tareas-lan-2026-09-10.md' = 'traspaso-tecnico.md'
        'docs/inventario-modular/instalacion-tareas-lan-2026-09-10.md' = 'INSTALACION.md'
        'src/main/resources/db/migration/V15__avisos_tareas_lan.sql' = 'V15__avisos_tareas_lan.sql'
        'android/README.md' = 'ANDROID.md'
    }
    foreach ($source in $files.Keys) {
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Falta $source" }
    }
    # Leer JUnit como XML evita depender de expresiones sobre logs y no transporta su salida sensible.
    $reports = @(Get-ChildItem -LiteralPath 'target/surefire-reports' -Filter 'TEST-*.xml')
    if ($reports.Count -eq 0) { throw 'Faltan reportes Maven.' }
    $tests = 0; $failures = 0; $errors = 0; $skipped = 0
    foreach ($report in $reports) {
        [xml]$xml = Get-Content -LiteralPath $report.FullName -Raw
        $tests += [int]$xml.testsuite.tests
        $failures += [int]$xml.testsuite.failures
        $errors += [int]$xml.testsuite.errors
        $skipped += [int]$xml.testsuite.skipped
    }
    if ($tests -eq 0 -or $failures -or $errors -or $skipped) { throw 'Pruebas incompletas o fallidas.' }
    $dest = Join-Path $root 'output/entrega-lan'
    $zip = Join-Path $root 'output/entrega-lan.zip'
    if ((Test-Path -LiteralPath $dest) -or (Test-Path -LiteralPath $zip)) {
        throw 'Ya existe un kit. Conservarlo o moverlo explicitamente antes de generar otro.'
    }
    New-Item -ItemType Directory -Path $dest | Out-Null
    foreach ($entry in $files.GetEnumerator()) {
        Copy-Item -LiteralPath $entry.Key -Destination (Join-Path $dest $entry.Value)
    }
    git bundle create (Join-Path $dest 'inventario-modular.bundle') primeros-pasos
    if ($LASTEXITCODE -ne 0) { throw 'Fallo la creacion del bundle.' }
    git bundle verify (Join-Path $dest 'inventario-modular.bundle')
    if ($LASTEXITCODE -ne 0) { throw 'Bundle invalido.' }
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    $version = "Inventario Modular - entrega LAN`nCommit: $commit`nRama: $branch`n"
    $version += "Preparado: $([DateTimeOffset]::Now.ToString('o'))`nAPK: piloto debug, NO release productiva.`n"
    $version += "No incluye secretos, base de datos ni herramientas Linux.`nLeer INSTALACION.md antes de desplegar.`n"
    [IO.File]::WriteAllText((Join-Path $dest 'VERSION.txt'), $version, $utf8)
    $summary = "Maven: $tests pruebas, $failures fallos, $errors errores, $skipped omitidas.`n"
    $summary += "Reportes de la compilacion local. Verificar vigencia antes de cada nueva entrega.`n"
    $summary += "No equivale a prueba de AD/MySQL institucional ni telefono fisico.`n"
    [IO.File]::WriteAllText((Join-Path $dest 'PRUEBAS.txt'), $summary, $utf8)
    $hashes = Get-ChildItem -LiteralPath $dest -File | Sort-Object Name | ForEach-Object {
        "{0}  {1}" -f (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(), $_.Name
    }
    [IO.File]::WriteAllText((Join-Path $dest 'SHA256SUMS'), ($hashes -join "`n") + "`n", $utf8)
    Compress-Archive -LiteralPath $dest -DestinationPath $zip
    Get-FileHash -LiteralPath $zip -Algorithm SHA256
    Write-Output "Kit generado: $zip"
} finally {
    Pop-Location
}
