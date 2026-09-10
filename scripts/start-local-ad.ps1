param(
    [string]$ServerPort = "8081",
    [string]$MysqlHost = "127.0.0.1",
    [string]$MysqlPort = "3306",
    [string]$MysqlDatabase = "inventario_modular",
    [string]$MysqlDefaultUser = "inventario_local",
    [string]$LdapUrl = "ldap://10.15.0.41:389",
    [string]$LdapDomain = "podjudsp.local",
    [string]$LdapBaseDn = "OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local",
    [string]$LocalAdminPassword = "AdminLocal123"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

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

Write-Host "Inventario Modular local + Active Directory" -ForegroundColor Cyan
Write-Host "Base de datos: MySQL local (${MysqlHost}:$MysqlPort/$MysqlDatabase), sin tocar MySQL de produccion."
Write-Host "LDAP: $LdapUrl / $LdapDomain"
Write-Host ""

$mysqlUser = Read-Host -Prompt "Usuario MySQL LOCAL [$MysqlDefaultUser]"
if ([string]::IsNullOrWhiteSpace($mysqlUser)) {
    $mysqlUser = $MysqlDefaultUser
}
$mysqlPassword = Read-SecretPlain -Prompt "Clave MySQL LOCAL para $mysqlUser"

$ldapUser = Read-Host -Prompt "Usuario lector AD (usuario@podjudsp.local o PODJUDSP\usuario)"
if ($ldapUser -notmatch "[@\\]") {
    $ldapUser = "$ldapUser@$LdapDomain"
}
$ldapPassword = Read-SecretPlain -Prompt "Clave AD para $ldapUser"

$localIpv4 = (Get-NetIPConfiguration |
    Where-Object { $_.IPv4DefaultGateway -and $_.IPv4Address } |
    ForEach-Object { $_.IPv4Address.IPAddress } |
    Where-Object { $_ -notlike "169.254.*" -and $_ -ne "127.0.0.1" } |
    Select-Object -First 1)

$jdbcUrl = "jdbc:mysql://$MysqlHost`:$MysqlPort/$MysqlDatabase`?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=America/Argentina/Buenos_Aires"

$env:SPRING_PROFILES_ACTIVE = "local"
$env:INVENTARIO_SERVER_PORT = $ServerPort
$env:INVENTARIO_LOCAL_AUTH_ENABLED = "true"
$env:INVENTARIO_LOCAL_AUTH_USERNAME = "admin.local"
$env:INVENTARIO_LOCAL_AUTH_PASSWORD = $LocalAdminPassword
$env:INVENTARIO_LOCAL_DB_AUTH_ENABLED = "true"
$env:INVENTARIO_MOVIL_APK_PATH = Join-Path $repoRoot "output\android\inventario-tareas-lan-piloto.apk"

$env:INVENTARIO_DB_PRIMARY_URL = $jdbcUrl
$env:INVENTARIO_DB_PRIMARY_USER = $mysqlUser
$env:INVENTARIO_DB_PRIMARY_PASSWORD = $mysqlPassword
$env:INVENTARIO_DB_FALLBACK_URL = $jdbcUrl
$env:INVENTARIO_DB_FALLBACK_USER = $mysqlUser
$env:INVENTARIO_DB_FALLBACK_PASSWORD = $mysqlPassword

$env:INVENTARIO_LDAP_ENABLED = "true"
$env:INVENTARIO_LDAP_URL = $LdapUrl
$env:INVENTARIO_LDAP_DOMAIN = $LdapDomain
$env:INVENTARIO_LDAP_BASE_DN = $LdapBaseDn
$env:INVENTARIO_LDAP_DISPLAY_NAME_ATTRIBUTE = "displayName"
$env:INVENTARIO_LDAP_FUERO_ATTRIBUTE = "department"
$env:INVENTARIO_LDAP_READ_ONLY_USER_DN = $ldapUser
$env:INVENTARIO_LDAP_READ_ONLY_PASSWORD = $ldapPassword
$env:INVENTARIO_LDAP_USER_SEARCH_BASE = ""
$env:INVENTARIO_LDAP_USER_SEARCH_FILTER = "(&(objectClass=user)(!(objectClass=computer)))"
$env:INVENTARIO_LDAP_USER_SEARCH_LIMIT = "50"

Write-Host ""
Write-Host "Arrancando en http://localhost:$ServerPort" -ForegroundColor Green
if ($localIpv4) {
    Write-Host "Desde el celular, pruebe: http://$localIpv4`:$ServerPort/movil/login" -ForegroundColor Green
}
Write-Host "MySQL local: ${MysqlHost}:$MysqlPort/$MysqlDatabase con usuario $mysqlUser"
Write-Host "Usuario local de prueba: admin.local / $LocalAdminPassword"
Write-Host "Para detener: Ctrl+C en esta ventana."
Write-Host ""

.\mvnw.cmd spring-boot:run
