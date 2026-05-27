# Configuración de Active Directory / LDAP - Inventario GOLD

Este documento resume la configuración y lógica de negocio establecida para el sistema de autenticación de Active Directory.

## 1. Datos del Servidor (Configurados en `.env`)
- **AUTH_MODE:** `hybrid` (Permite entrar con usuarios de AD y usuarios locales).
- **AD_SERVER:** `10.15.0.41`
- **AD_DOMAIN:** `podjudsp.local`
- **AD_BASE_DN:** `OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local`
- **AD_USE_SSL:** `false` (Puerto 389)
- **AD_SUPERUSERS:** `gmurad_adm,administrador` (Solo estos usuarios son admins automáticos).

## 2. Lógica de Negocio y Permisos
El sistema sigue un modelo de **Promoción Manual por Seguridad**:

1. **Ingreso por defecto:** Cualquier técnico de informática con cuenta en AD puede loguearse usando su usuario (ej: `gmurad`) y clave de red.
2. **Rol inicial:** Al entrar por primera vez, el sistema crea el usuario localmente con el rol `tecnico` y solo acceso a la **Interfaz Móvil**.
3. **Promoción:** Un administrador debe ingresar a la gestión de usuarios del Dashboard y habilitar manualmente el permiso de "Acceso al Dashboard" para que ese técnico pueda ver la gestión centralizada de equipos.
4. **Resistencia a fallos:** El usuario local `administrador` siempre está disponible para acceso de emergencia si el servidor de AD no responde o si estás trabajando fuera de la red (casa).

## 3. Comandos para Actualización en Servidor Ubuntu

Para aplicar estos cambios en producción:

```bash
# 1. Acceder al directorio
cd /opt/inventario

# 2. Editar el archivo .env manualmente (ya que no se sube a Git)
nano .env
# [Pegar la configuración del punto 1 arriba]

# 3. Reiniciar el servicio
sudo systemctl restart inventario

# 4. (Opcional) Ver logs en tiempo real para confirmar el login
sudo journalctl -u inventario -f
```

---
**Fecha de configuración:** 9 de Abril de 2026
**Usuario responsable:** Gustavo Murad
