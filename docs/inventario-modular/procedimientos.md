# Procedimientos Operativos - Inventario Modular

Este documento deja por escrito los pasos que venimos usando para trabajar con el
Inventario Modular. El objetivo es que el servidor, las pruebas y la subida a GitHub no
dependan de memoria ni de una sesion abierta del agente.

## Alcance

- Proyecto activo: `inventario-modular/`.
- Puerto local: `8081`.
- URL de red: `http://192.168.1.8:8081/`.
- Inventario Next queda pausado/deshabilitado como foco de trabajo.
- Inventario viejo Flask sigue siendo el sistema operativo real hasta migrar modulo por
  modulo.

## Apagar Inventario Next

Usar solo si quedo algun servidor de Next activo en desarrollo:

```powershell
Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,State,OwningProcess
```

Si aparece un proceso escuchando y corresponde a Next:

```powershell
Stop-Process -Id <PID> -Force
```

## Levantar Inventario Modular

Desde la raiz del repo:

```powershell
cd inventario-modular
.\mvnw.cmd spring-boot:run
```

Para dejarlo corriendo en segundo plano desde la raiz del repo:

```powershell
Start-Process -WindowStyle Hidden `
  -FilePath 'G:\unju2025\google gravity\ServidorInventario\inventario-modular\mvnw.cmd' `
  -ArgumentList 'spring-boot:run' `
  -WorkingDirectory 'G:\unju2025\google gravity\ServidorInventario\inventario-modular' `
  -RedirectStandardOutput 'G:\unju2025\google gravity\ServidorInventario\inventario-modular\modular-server.out.log' `
  -RedirectStandardError 'G:\unju2025\google gravity\ServidorInventario\inventario-modular\modular-server.err.log'
```

## Verificar que responde

```powershell
Get-NetTCPConnection -LocalPort 8081 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,State,OwningProcess
```

```powershell
Invoke-WebRequest -UseBasicParsing 'http://192.168.1.8:8081/' -TimeoutSec 8
Invoke-WebRequest -UseBasicParsing 'http://192.168.1.8:8081/login' -TimeoutSec 8
Invoke-WebRequest -UseBasicParsing 'http://192.168.1.8:8081/api/v1/health' -TimeoutSec 8
```

Resultado esperado:

- `/` redirige y termina mostrando la pantalla de login.
- `/login` responde HTML con `Inventario Modular`, campos de usuario/clave habilitados y
  selector `Local` / `Dominio`.
- El modo `Local` permite ingresar con el administrador configurado por
  `BOOTSTRAP_ADMIN_USERNAME` / `BOOTSTRAP_ADMIN_PASSWORD`.
- `/api/v1/health` responde JSON con `status: ok`.
- `/api/v1/modules` responde `401` sin autenticacion.
- `/api/v1/modules` responde `200` si se consulta con una sesion autenticada.

## Ejecutar pruebas

```powershell
cd inventario-modular
.\mvnw.cmd test
```

Antes de subir cambios, el resultado esperado es `BUILD SUCCESS`.

## Guardar cambios en GitHub

Revisar primero que no se incluyan certificados, logs, `target/` ni secretos:

```powershell
git status --short
git diff --staged --check
```

Agregar solo los archivos del modulo/documentacion que correspondan:

```powershell
git add inventario-modular docs/inventario-modular CONTEXT.md
```

Crear commit:

```powershell
git commit -m "feat: add modular login shell and procedures"
```

Subir a GitHub:

```powershell
git push github codex/inventario-modular
```

Regla del proyecto: cuando tambien se suba a GitLab, se debe hacer push a GitHub. En esta
rama de trabajo ya estamos preservando los cambios en GitHub.
