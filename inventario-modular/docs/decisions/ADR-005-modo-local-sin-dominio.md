# ADR-005: Modo Local Sin Dominio Para Desarrollo En Casa

## Status

Aceptada

## Fecha

2026-08-28

## Contexto

Inventario Modular ya pudo validar usuarios contra Active Directory real en el trabajo.
Eso confirma que el camino productivo correcto es LDAP/AD.

Pero desde casa no hay acceso al dominio ni a la base MySQL institucional. Si el sistema
dependiera exclusivamente de AD, no se podria estudiar ni desarrollar localmente en
Windows. El inventario viejo resolvia una situacion parecida usando claves locales cuando
detectaba que no estaba en la red del dominio.

## Decision

Agregar un modo local explicito para desarrollo:

- LDAP apagado: `inventario.ldap.enabled=false`.
- Login local encendido: `inventario.local-auth.enabled=true`.
- Usuario local configurado por propiedades o variables de entorno.
- Base MySQL local en `127.0.0.1:3306`.

El modo local no intenta detectar automaticamente la red. Se activa por configuracion para
que sea claro que se esta trabajando en casa/desarrollo.

## Alternativas Consideradas

### Detectar automaticamente si hay dominio

Ventaja: se parece al comportamiento del sistema viejo.

Desventaja: puede generar falsos positivos y hacer dificil entender por que se eligio un
modo de login.

Resultado: descartado por ahora.

### Usar siempre Active Directory

Ventaja: maxima fidelidad con produccion.

Desventaja: impide trabajar desde casa sin VPN/dominio.

Resultado: descartado para desarrollo local.

### Usar un modo local activado por configuracion

Ventaja: simple, explicito, testeable y facil de explicar.

Desventaja: requiere recordar que en el trabajo debe activarse LDAP real.

Resultado: aceptado.

## Consecuencias

- Se puede desarrollar en casa sin dominio.
- Produccion sigue usando Active Directory real.
- El modo local debe estar documentado y probado.
- Las claves locales son solo de desarrollo y no representan usuarios reales del dominio.
- En etapas futuras, la autorizacion por modulos vivira en MySQL y no en este usuario en
  memoria.
