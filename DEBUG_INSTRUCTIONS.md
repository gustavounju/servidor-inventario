# Instrucciones de Diagnóstico - Servidor Inventario

## `debug_inventario.ps1`

Este script sirve para verificar la conectividad y el envío de datos desde una PC cliente hacia el servidor de inventario, sin afectar los datos reales de manera crítica (usa un payload de prueba).

### ¿Para qué sirve?
1.  **Verificar Conexión de Red:** Comprueba si la PC alcanza al servidor por el puerto 5000 (TCP).
2.  **Verificar Identidad:** Muestra qué nombre de equipo (`hostname`) está detectando el sistema.
3.  **Probar Envío de Datos:** Envía un paquete JSON de prueba para asegurar que el servidor recibe y procesa la información correctamente.
4.  **Ver Error Real:** Si falla, muestra la respuesta completa del servidor para facilitar la depuración.

### ¿Cómo usarlo en otra PC?

1.  **Copiar el archivo:**
    Copia el archivo `debug_inventario.ps1` al escritorio o carpeta temporal de la PC a probar.

2.  **Ejecutar con PowerShell:**
    Haz clic derecho sobre el archivo y selecciona **"Ejecutar con PowerShell"**.
    
    *O abre una terminal de PowerShell, navega a la carpeta y ejecuta:*
    ```powershell
    .\debug_inventario.ps1
    ```

3.  **Analizar Resultados:**
    - Si ves **"TcpTestSucceeded : True"** -> La red está bien.
    - Si ves **"EXITO. Respuesta del Servidor: success"** -> Todo funciona correctamente.
    - Si ves errores en rojo, toma una captura de pantalla o copia el mensaje para soporte.
