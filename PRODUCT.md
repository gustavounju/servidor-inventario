# Product

## Register

product

## Users
El sistema es utilizado por dos perfiles principales simultáneamente: técnicos que necesitan registrar tareas diarias y resolver tickets de forma ágil, y administradores que requieren monitorear el estado general de la infraestructura (racks, equipos, métricas) de un vistazo.

## Product Purpose
Servir como el centro de control unificado para el Departamento de Informática del Centro Judicial San Pedro. Su objetivo es mantener el inventario al día y asegurar que las tareas de mantenimiento y auditoría (como la toma de temperaturas en racks) se realicen y visualicen con fricción cero.

## Brand Personality
Moderno, limpio, profesional y con una estética de **"Centro de Operaciones / Cyberpunk"**. El enfoque absoluto está en la claridad visual: la información debe respirar y las acciones deben ser evidentes sin esfuerzo cognitivo. 
El sistema no debe verse como un software ofimático genérico, sino como un **panel de control táctico avanzado** (Dark theme por defecto, contrastes altos, barras de estado y jerarquía tipo consola).

## Anti-references
Herramientas saturadas de botones y menús complejos donde no se sabe qué tocar. Se debe evitar la interfaz sobrecargada ("bloatware"), el uso de elementos decorativos sin función y el amontonamiento de datos que cause parálisis por análisis.

## Design Principles
1. **Estética "Midnight" Estricta**: Uso prioritario de fondos oscuros con tipografías y bordes en colores semánticos vibrantes (Ej: neón verde para estable, naranja/ámbar para advertencias, rojo para crítico). El archivo `gold.css` es la base de este estilo.
2. **Claridad sobre densidad**: Es preferible un poco más de scroll que una interfaz asfixiante. Cada pantalla debe tener una jerarquía obvia mediante el uso de "Priority Tickets" o paneles.
3. **Acción evidente**: Las acciones principales de los técnicos (ej: añadir tarea) deben estar siempre a un clic de distancia, sin menús anidados.
4. **Escaneo inmediato**: Los administradores deben poder evaluar el estado del sistema (KPIs, alarmas de racks) escaneando barras de progreso (estilo Radar), colores y números sin tener que leer párrafos de texto.
5. **Micro-interacciones funcionales**: Uso de animaciones de esqueleto (Skeleton Loaders) y contadores dinámicos (Count-Ups) para evitar parpadeos y dar una sensación de fluidez y de "sistema vivo".

## Accessibility & Inclusion
Soporte forzoso y fluido para modo Claro y Oscuro, garantizando contraste adecuado (WCAG AA mínimo) en ambos esquemas de color para aliviar la fatiga visual del equipo durante toda la jornada.
