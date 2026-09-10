param(
    [string]$MysqlHost = "127.0.0.1",
    [string]$MysqlPort = "3306",
    [string]$MysqlDatabase = "inventario_modular",
    [string]$AppUser = "inventario_local",
    [string]$AppPassword = "Cambiar_Clave_Local_123!",
    [string]$RootUser = "root"
)

$ErrorActionPreference = "Stop"

function Read-SecretPlain {
    param([string]$Prompt)

    $secure = Read-Host -Prompt $Prompt -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        if ($bstr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }
}

function Escape-MySqlLiteral {
    param([string]$Value)
    $Value -replace "\\", "\\\\" -replace "'", "''"
}

if ($MysqlDatabase -notmatch "^[A-Za-z0-9_]+$") {
    throw "Nombre de base no valido: $MysqlDatabase"
}
if ($AppUser -notmatch "^[A-Za-z0-9_]+$") {
    throw "Nombre de usuario no valido: $AppUser"
}

$mysqlExe = Get-Command mysql.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source
if (-not $mysqlExe) {
    $candidates = @(
        "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe",
        "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
        "C:\Program Files\MySQL\MySQL Workbench 8.0 CE\mysql.exe"
    )
    $mysqlExe = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $mysqlExe) {
    throw "No encontre mysql.exe. Instale MySQL client o agregue MySQL Server bin al Path."
}

Write-Host "Preparando MySQL local para Inventario Modular" -ForegroundColor Cyan
Write-Host "Servidor: ${MysqlHost}:$MysqlPort"
Write-Host "Base: $MysqlDatabase"
Write-Host "Usuario de app: $AppUser"
Write-Host "Cliente: $mysqlExe"
Write-Host ""

$rootPassword = Read-SecretPlain -Prompt "Clave MySQL de $RootUser"

$escapedDatabase = "``$MysqlDatabase``"
$escapedAppUser = Escape-MySqlLiteral $AppUser
$escapedAppPassword = Escape-MySqlLiteral $AppPassword

$sql = @"
CREATE DATABASE IF NOT EXISTS $escapedDatabase
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '$escapedAppUser'@'localhost'
  IDENTIFIED BY '$escapedAppPassword';

ALTER USER '$escapedAppUser'@'localhost'
  IDENTIFIED BY '$escapedAppPassword';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
  ON $escapedDatabase.* TO '$escapedAppUser'@'localhost';

FLUSH PRIVILEGES;
"@

$oldMysqlPwd = $env:MYSQL_PWD
$env:MYSQL_PWD = $rootPassword
try {
    $sql | & $mysqlExe --host=$MysqlHost --port=$MysqlPort --protocol=tcp --user=$RootUser --default-character-set=utf8mb4
    if ($LASTEXITCODE -ne 0) {
        throw "mysql.exe finalizo con codigo $LASTEXITCODE"
    }
} finally {
    if ($null -eq $oldMysqlPwd) {
        Remove-Item Env:\MYSQL_PWD -ErrorAction SilentlyContinue
    } else {
        $env:MYSQL_PWD = $oldMysqlPwd
    }
}

Write-Host ""
Write-Host "MySQL local listo." -ForegroundColor Green
Write-Host "Ahora arranque la app con: .\scripts\start-local-ad.ps1"
Write-Host "Cuando pida clave de $AppUser, use la clave local configurada en este script."
