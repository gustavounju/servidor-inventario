# ADR-004: Login Active Directory solo lectura

## Estado

Aceptado.

## Fecha

2026-08-28

## Contexto

Inventario Modular necesita autenticacion institucional, pero todavia esta en etapa de
laboratorio. El sistema viejo ya tenia integracion con Active Directory y se pudo leer su
configuracion de forma segura desde la copia local y desde el `.env` del servidor viejo,
sin mostrar claves.

Datos confirmados desde el servidor viejo:

```text
AD_SERVER=10.15.0.41
AD_DOMAIN=podjudsp.local
AD_BASE_DN=OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local
AD_USE_SSL=false
AD_CONNECT_TIMEOUT=5
```

El sistema viejo tambien muestra que los atributos utiles para esta primera pantalla son:

```text
sAMAccountName -> usuario
displayName -> nombre visible
department -> fuero
telephoneNumber -> telefono
mail -> correo
```

## Decision

Inventario Modular autentica contra Active Directory usando Spring Security LDAP, pero en
esta etapa solo lee datos del usuario que inicia sesion.

No se implementa todavia sincronizacion masiva de usuarios ni escritura sobre AD.

Variables equivalentes para el nuevo sistema:

```text
INVENTARIO_LDAP_ENABLED=true
INVENTARIO_LDAP_URL=ldap://10.15.0.41:389
INVENTARIO_LDAP_DOMAIN=podjudsp.local
INVENTARIO_LDAP_BASE_DN=OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local
INVENTARIO_LDAP_DISPLAY_NAME_ATTRIBUTE=displayName
INVENTARIO_LDAP_FUERO_ATTRIBUTE=department
```

## Alternativas consideradas

### Usar usuario tecnico de sincronizacion

El sistema viejo tenia `AD_SYNC_USER` y `AD_SYNC_PASSWORD` para listar usuarios y poblar
tablas locales.

Se descarta para esta primera etapa porque el objetivo actual es solo validar login y
mostrar datos del usuario autenticado. No necesitamos traer todo el directorio ni guardar
usuarios locales.

### Copiar la logica completa del sistema viejo

El sistema viejo tiene modo hibrido, usuarios sombra, permisos locales, roles y aprobacion
manual.

Se descarta por ahora porque seria demasiado alcance para el primer inicio del sistema
nuevo. Esa logica se retomara cuando se disenien roles reales y permisos de modulos.

### Hacer login local temporal

Spring Security permite login local de desarrollo si AD esta desactivado.

Se mantiene solo como ayuda de laboratorio, con `INVENTARIO_LDAP_ENABLED=false` por
defecto. En Ubuntu, la prueba real debe activar AD.

## Consecuencias

- `/admin` requiere login.
- El login usa la clave de red del usuario contra AD.
- La app muestra usuario, nombre visible, fuero y atributos no sensibles recibidos.
- La app no necesita conocer ni guardar la clave del usuario.
- La app no escribe datos en AD.
- Si AD no responde o la configuracion es incorrecta, el login falla y hay que revisar
  variables, red y logs.
- HTTPS queda para una etapa posterior con nginx/reverse proxy; por ahora la prueba es
  HTTP interno en `8081`.

