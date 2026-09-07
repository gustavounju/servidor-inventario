# Versionado Git

Apuntes practicos de versionado para Inventario Modular.

## Que es un remoto

Un remoto es un alias local que Git usa para recordar la direccion de un repositorio
externo.

En este proyecto hay dos remotos:

```text
origin  -> GitLab
github  -> GitHub
```

El nombre `github` no es una palabra especial de Git. Es un alias elegido para identificar
el repositorio publicado en GitHub.

## Ver remotos configurados

Para ver los remotos de este proyecto:

```powershell
cd "G:\unju2025\google gravity\inventario-modular"
git remote -v
```

Salida esperada:

```text
origin  https://gitlab.com/gustavoeliasm/inventario-modular.git (fetch)
origin  https://gitlab.com/gustavoeliasm/inventario-modular.git (push)
github  https://github.com/gustavounju/inventario-modular.git (fetch)
github  https://github.com/gustavounju/inventario-modular.git (push)
```

## Que significa `git push github primeros-pasos`

Comando:

```powershell
git push github primeros-pasos
```

Significado:

- `git push`: subir commits desde la maquina local hacia un repositorio remoto.
- `github`: remoto de destino. En este proyecto apunta a GitHub.
- `primeros-pasos`: rama que se quiere subir.

Lectura completa:

```text
Subir la rama local primeros-pasos al remoto github.
```

## Diferencia entre GitLab y GitHub en este proyecto

Decision de trabajo:

- GitLab puede ser gestionado automaticamente por el asistente.
- GitHub lo gestiona Gustavo por comandos para practicar versionado.

Por eso, cuando el asistente sube un commit a GitLab, Gustavo sincroniza GitHub con:

```powershell
cd "G:\unju2025\google gravity\inventario-modular"
git push github primeros-pasos
```

## Que significa `-u`

El primer push a un remoto puede usar:

```powershell
git push -u github primeros-pasos
```

La opcion `-u` significa `--set-upstream`. Sirve para dejar conectada la rama local con la
rama remota.

Despues de usar `-u`, Git sabe que la rama local `primeros-pasos` tiene como rama remota
asociada `github/primeros-pasos`.

## Que significa `ahead`

Si `git status` muestra:

```text
## primeros-pasos...github/primeros-pasos [ahead 1]
```

significa que la rama local tiene 1 commit que todavia no esta subido a GitHub.

Para subirlo:

```powershell
git push github primeros-pasos
```

## Regla del proyecto

GitLab y GitHub deben quedar con la misma rama `primeros-pasos` y los mismos commits.
