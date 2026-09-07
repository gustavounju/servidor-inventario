# ADR-006: Autorizacion Modular Inicial

## Estado

Aceptada.

## Contexto

Inventario Modular ya pudo validar usuarios contra Active Directory en el entorno de
trabajo. Eso resolvio la identidad, pero no resuelve que puede hacer cada persona dentro
del sistema.

El requisito funcional es que los modulos puedan prenderse y apagarse por usuario o rol.
Por ejemplo:

- un administrador debe ver todo;
- un tecnico puede necesitar `EQUIPOS`, `STOCK`, `COMPONENTES` y `TAREAS`;
- una persona de patrimonio puede necesitar `MUEBLES`, `PATRIMONIO`, `COMPONENTES` y
  `REPORTES`;
- un usuario lector puede tener solo consulta.

## Decision

Se crea una autorizacion local propia en MySQL, separada de Active Directory.

Active Directory queda como fuente de autenticacion:

```text
usuario + clave de dominio
```

Inventario Modular queda como fuente de autorizacion:

```text
usuarios + roles + modulos + permisos
```

La primera migracion Flyway crea las tablas de seguridad modular y carga un seed inicial
con modulos, permisos, roles y el usuario local `admin.local`.

## Consecuencias positivas

- No se guardan claves de dominio.
- La autorizacion queda bajo control del sistema Java.
- La futura app movil puede consultar los modulos permitidos por API.
- El modelo sirve tanto para Windows local como para Ubuntu/trabajo.
- Se puede avanzar por modulos sin rehacer la seguridad cada vez.

## Consecuencias negativas o pendientes

- Todavia falta una pantalla para administrar usuarios y roles.
- Todavia falta aplicar bloqueo fino por permiso en cada modulo funcional.
- En produccion debe cargarse un usuario administrador real del dominio antes de endurecer
  el bloqueo.

## Regla practica

No construir `EQUIPOS`, `MUEBLES`, `STOCK`, `ACTAS` o `REPORTES` como pantallas aisladas.
Cada modulo nuevo debe consultar esta capa de autorizacion antes de exponer datos o
acciones.
