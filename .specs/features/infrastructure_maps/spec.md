# Planos (Infrastructure Maps) - Enhancements Specification

## Problem Statement

El módulo de planos de infraestructura (`bp_maps.py`) permite ubicar recursos (PCs, impresoras, usuarios) en mapas físicos. Sin embargo, actualmente no queda registro histórico de cuándo un recurso fue movido (auditabilidad), y no existe una manera sencilla de exportar el estado actual del mapa para reportes físicos o compartir con terceros. 

## Goals

- [ ] Registrar automáticamente un evento en el historial cuando un activo cambia de posición (o se retira del mapa).
- [ ] Permitir a los usuarios visualizar el historial de ubicaciones de un activo directamente desde el mapa.
- [ ] Permitir la exportación del mapa con sus activos superpuestos a un formato de imagen estático.

## Out of Scope

| Feature     | Reason         |
| ----------- | -------------- |
| Rastreo GPS o RFID automático | El sistema se basa en actualizaciones manuales por parte del equipo. |
| Integración de planos en CAD/BIM | Se seguirán usando imágenes planas subidas por los usuarios. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default  | Rationale | Confirmed? |
| --------------------- | --------------- | --------- | ---------- |
| Método de exportación | Exportación vía frontend (`html2canvas`) a PNG | Evita depender de herramientas pesadas en el backend (ej. Selenium/Puppeteer) y respeta las posiciones que el navegador ya calculó. | n |
| Estructura del historial | Nueva tabla DB: `asset_location_history` | Minimiza cambios en las tablas actuales y centraliza la auditoría de movimientos geográficos. | n |
| Profundidad del historial | Mostrar últimos 10 movimientos por activo en un modal | Mantiene la interfaz limpia y rápida para los técnicos en campo. | n |

**Open questions:** none — all resolved or logged above.

---

## User Stories

### P1: Historial de Posición ⭐ MVP

**User Story**: As a técnico, I want ver cuándo y adónde se movió un activo, so that puedo rastrear su ubicación física en caso de extravío o auditoría.

**Why P1**: Auditabilidad esencial para inventario físico.

**Acceptance Criteria**:

1. WHEN un activo cambia de `map_id` o coordenadas (vía arrastrar y soltar) THEN system SHALL registrar un evento en `asset_location_history` con usuario, fecha y nueva posición.
2. WHEN se hace clic en "Ver Historial" de un activo en el mapa THEN system SHALL mostrar un listado cronológico inverso de las ubicaciones.

**Independent Test**: Modificar la posición de una PC en el mapa y verificar que la base de datos registra el movimiento.

---

### P1: Exportar Mapa ⭐ MVP

**User Story**: As a técnico/administrador, I want descargar el mapa con la distribución de los equipos so that puedo imprimirlo o enviarlo en un informe.

**Why P1**: Reportes e impresión.

**Acceptance Criteria**:

1. WHEN el usuario hace clic en "Exportar Mapa" THEN system SHALL generar una imagen combinando el plano base y los íconos/nombres de los equipos en sus coordenadas actuales.

**Independent Test**: Verificar que el archivo descargado contiene la imagen del plano y los marcadores superpuestos correctamente escalados.

---

## Requirement Traceability

| Requirement ID | Story       | Phase  | Status  |
| -------------- | ----------- | ------ | ------- |
| MAPS-01        | P1: Historial | Design | Pending |
| MAPS-02        | P1: Exportar  | Design | Pending |

## Success Criteria

- [ ] Todas las operaciones de drag & drop dejan registro auditable en la base de datos.
- [ ] La exportación funciona sin requerir dependencias gráficas pesadas en el servidor Ubuntu.
