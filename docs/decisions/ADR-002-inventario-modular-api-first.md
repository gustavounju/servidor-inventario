# ADR-002: Inventario Modular API-first Para Futura App Movil

## Status

Accepted

## Date

2026-08-28

## Context

El inventario original sigue funcionando para flujos importantes como equipos, actas y
operaciones tecnicas. Sin embargo, tiene deuda tecnica y no ofrece una arquitectura modular
limpia para crecer hacia muebles, patrimonio, componentes, stock, usuarios y reportes.

El intento previo de modernizar el frontend no resolvio de forma confiable la autenticacion
con Active Directory y genero friccion operativa. El nuevo sistema debe construirse desde
cero en Java, alineado con la formacion universitaria del responsable y con tecnologias
defendibles en un entorno institucional.

Existe ademas un requerimiento futuro importante: tecnicos y usuarios operativos podrian
usar una app movil. La arquitectura no debe obligar a rehacer el backend cuando llegue esa
app.

## Decision

Construir Inventario Modular como un sistema Java con Spring Boot y arquitectura API-first.

El backend sera la fuente de verdad para:

- Autenticacion contra Active Directory.
- Autorizacion local por usuarios, roles, permisos y modulos.
- Reglas de negocio de inventario.
- API versionada para clientes futuros.

La web administrativa existira solo como cliente del sistema, no como lugar exclusivo de
la logica de negocio. La futura app movil debera poder consumir la misma API.

## Consequences

- El sistema queda preparado para app movil sin reescribir reglas centrales.
- Los permisos se aplican de forma consistente en web, API y futuros clientes.
- La primera etapa debe invertir mas en seguridad y contratos de API.
- No conviene poner logica critica dentro de templates HTML.
- El backend debe devolver errores claros: 401 para no autenticado, 403 para no autorizado.

## Alternatives Considered

### Web responsive primero

Pros:

- Permite avanzar rapido con una sola interfaz.
- Tecnicos pueden usar navegador del celular.

Cons:

- Puede esconder logica en pantallas HTML.
- No garantiza que una app futura pueda reutilizar todo.
- No responde a la preferencia actual de priorizar app movil futura.

Decision: rechazada como objetivo principal. Puede existir una web administrativa, pero no
sera el eje del diseno.

### App movil nativa primero

Pros:

- Ataca directamente el objetivo movil.
- Puede mejorar experiencia en campo.

Cons:

- Requiere resolver backend, autenticacion, permisos y app al mismo tiempo.
- Aumenta el riesgo inicial.
- Puede demorar el primer nucleo funcional.

Decision: rechazada para la primera etapa. Primero se construye el backend API-first.

### API-first con panel administrativo minimo

Pros:

- Prepara app movil futura sin rehacer backend.
- Mantiene el primer alcance controlado.
- Permite probar seguridad y permisos antes de migrar modulos.
- Encaja bien con Spring Boot y MySQL.

Cons:

- Requiere disenar contratos de API desde el inicio.
- No entrega una app movil completa en el primer hito.

Decision: aceptada.

## Implementation Notes

- Usar Java 21 LTS.
- Usar Maven como herramienta de build.
- Usar MySQL local `inventario_modular` en desarrollo.
- Usar Flyway para migraciones.
- Usar Spring Security para autenticacion/autorizacion.
- Integrar Active Directory mediante LDAP.
- No guardar claves de dominio.
- En desarrollo/casa, usar MySQL local `inventario_modular`.
- En produccion, usar MySQL remoto `10.15.0.62:3306/inventario_modular` mediante el
  `EnvironmentFile` de systemd, sin versionar secretos.
