from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT = "output/pdf/manual-usuario-inventario-modular.pdf"


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1d252d"),
            spaceAfter=16,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#415366"),
            spaceAfter=20,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#23405f"),
            spaceBefore=10,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=16,
            textColor=colors.HexColor("#1d252d"),
            spaceBefore=8,
            spaceAfter=5,
        ),
        "case": ParagraphStyle(
            "case",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#23405f"),
            backColor=colors.HexColor("#eef5fb"),
            borderColor=colors.HexColor("#b8cadc"),
            borderWidth=0.5,
            borderPadding=6,
            spaceBefore=5,
            spaceAfter=7,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.8,
            leading=14,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#1d252d"),
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#526475"),
        ),
        "table_header": ParagraphStyle(
            "table_header",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=12,
            textColor=colors.white,
        ),
        "code": ParagraphStyle(
            "code",
            parent=base["BodyText"],
            fontName="Courier",
            fontSize=7.6,
            leading=10,
            textColor=colors.HexColor("#25313d"),
            backColor=colors.HexColor("#f6f8fa"),
            borderColor=colors.HexColor("#d9e0e7"),
            borderWidth=0.5,
            borderPadding=5,
            spaceAfter=7,
        ),
    }


S = styles()


def p(text, style="body"):
    if style == "code":
        return Preformatted(text, S["code"], maxLineLength=92)
    return Paragraph(text, S[style])


def bullets(items):
    flow = []
    for item in items:
        flow.append(p(f"- {item}"))
    return flow


def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#5e7184"))
    canvas.drawString(1.6 * cm, 1.0 * cm, "Inventario Modular - Manual de usuario")
    canvas.drawRightString(19.4 * cm, 1.0 * cm, f"Pagina {doc.page}")
    canvas.restoreState()


def info_table(rows):
    table = Table(rows, colWidths=[4.1 * cm, 11.4 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0f6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1d252d")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#f6f8fa")),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#d9e0e7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def workflow_table(rows):
    table = Table(rows, colWidths=[1.2 * cm, 4.2 * cm, 10.1 * cm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#23405f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#f6f8fa")),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#d9e0e7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def section(title, body):
    flow = [p(title, "h1")]
    flow.extend(body)
    return flow


def build():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="Manual de usuario - Inventario Modular",
        author="Departamento de Informatica - Centro Judicial San Pedro",
    )

    story = [
        Spacer(1, 3.4 * cm),
        p("Manual de usuario", "title"),
        p("Inventario Modular<br/>Centro Judicial San Pedro - Departamento de Informatica", "subtitle"),
        info_table([
            [p("Version", "small"), p("Primera guia operativa - 1 de septiembre de 2026", "small")],
            [p("Alcance", "small"), p("Alta de equipos, usuarios, ordenes de armado, diferencias, tareas, muebles, patrimonio y reportes.", "small")],
            [p("Acceso", "small"), p("La aplicacion se usa desde el panel administrativo protegido por login.", "small")],
        ]),
        PageBreak(),
    ]

    story += section("1. Ingreso al sistema", [
        p("Abra la direccion de Inventario Modular en el navegador. En laboratorio local suele ser:"),
        p("http://localhost:8081/login", "code"),
        p("En produccion se ingresa con la direccion que publique Sistemas. Despues del login se abre el panel principal en <b>/admin</b>."),
        *bullets([
            "Use su cuenta de Active Directory cuando el sistema este conectado al dominio.",
            "Use una cuenta local solamente cuando Sistemas la haya creado para desarrollo, rescate o tareas temporales.",
            "El menu muestra solo los modulos permitidos para el usuario actual.",
        ]),
    ])

    story += section("2. Alta y control de equipos", [
        p("El modulo <b>Equipos</b> es el inventario tecnico principal. Registra PCs y dispositivos con nombre, usuario, fuero, IP, sistema operativo, procesador, memoria, discos, perifericos y estado de monitoreo."),
        p("<b>Ruta:</b> /admin/equipos"),
        p("Proceso recomendado para alta manual:"),
        *bullets([
            "Entrar a Equipos desde el panel principal.",
            "Buscar primero por nombre de PC, usuario o fuero para evitar duplicados.",
            "Si el equipo existe, abrir el detalle y corregir datos desde edicion manual.",
            "Si el equipo llega por script, el sistema crea o actualiza el registro por nombre de equipo.",
            "Revisar el detalle del equipo para confirmar hardware, ultimo usuario y fecha de reporte.",
        ]),
        p("El script de inventario es el camino ideal para PCs reales porque captura informacion tecnica automaticamente. La carga manual queda para completar datos, corregir ubicacion o activar/desactivar equipos."),
    ])

    story += section("3. Caso de estudio: trabajar con un equipo", [
        p("Caso: Mesa de Entradas informa que la PC <b>PC-INF-001</b> quedo lenta y se planifica instalar un SSD de 480GB y confirmar la memoria instalada.", "case"),
        p("Objetivo operativo: dejar trazabilidad completa desde la busqueda del equipo hasta la evidencia exportable, sin depender de notas sueltas."),
        workflow_table([
            [p("Paso", "table_header"), p("Pantalla", "table_header"), p("Accion esperada", "table_header")],
            [p("1", "small"), p("/admin/equipos", "small"), p("Buscar <b>PC-INF-001</b>. Si no aparece, revisar si llego por script o cargar el alta manual minima.", "small")],
            [p("2", "small"), p("/admin/equipos/{id}", "small"), p("Abrir el detalle y confirmar nombre, ultimo usuario, fuero, IP, sistema operativo, RAM, discos y perifericos.", "small")],
            [p("3", "small"), p("/admin/stock", "small"), p("Verificar que exista el SSD disponible. Si es nuevo, cargarlo con tipo DISCO, marca, modelo, serial, capacidad y ubicacion.", "small")],
            [p("4", "small"), p("/admin/ordenes-armado", "small"), p("Crear una orden para PC-INF-001 con descripcion clara: instalar SSD 480GB y revisar RAM.", "small")],
            [p("5", "small"), p("/admin/ordenes-armado", "small"), p("Agregar el SSD como componente esperado. Si sale realmente del deposito, confirmar salida desde la orden.", "small")],
            [p("6", "small"), p("/login", "small"), p("Copiar el comando PowerShell del script, ejecutarlo en la PC y esperar que reporte al endpoint de inventario.", "small")],
            [p("7", "small"), p("/admin/equipos/{id}", "small"), p("Volver al detalle del equipo y comparar componentes esperados contra detectados en el gemelo digital.", "small")],
            [p("8", "small"), p("/admin/dashboard-diferencias", "small"), p("Filtrar por equipo o por estado. Si aparece FALTA, SOBRA o REVISAR, abrir el equipo y corregir la informacion.", "small")],
            [p("9", "small"), p("/admin/tareas", "small"), p("Crear una tarea tecnica si queda trabajo pendiente, por ejemplo clonar disco, cambiar cable SATA o validar rendimiento.", "small")],
            [p("10", "small"), p("/admin/actas", "small"), p("Emitir acta de entrega o intervencion cuando el equipo vuelva al usuario o quede formalmente intervenido.", "small")],
        ]),
        Spacer(1, 7),
        p("Criterio para interpretar diferencias:"),
        info_table([
            [p("Resultado", "small"), p("Decision operativa", "small")],
            [p("COINCIDE", "small"), p("El componente esperado fue detectado. Puede cerrarse la revision de esa pieza.", "small")],
            [p("FALTA", "small"), p("La orden esperaba la pieza, pero el reporte no la ve. Revisar instalacion fisica, serial o si el script corrio antes del cambio.", "small")],
            [p("SOBRA", "small"), p("La PC detecta una pieza no prevista. Registrar si pertenece al equipo o si debe corregirse stock/patrimonio.", "small")],
            [p("REVISAR", "small"), p("Hay coincidencia parcial. Confirmar serial, modelo o capacidad antes de darla por correcta.", "small")],
        ]),
        Spacer(1, 7),
        p("Evidencia para cerrar el caso:"),
        *bullets([
            "Descargar CSV del dashboard de diferencias filtrado por PC-INF-001.",
            "Consultar auditoria filtrando por usuario, modulo STOCK, ORDENES_ARMADO, COMPONENTES o ACTAS segun el cambio que se quiere revisar.",
            "Descargar CSV de auditoria si se necesita adjuntar trazabilidad a un informe interno.",
            "Guardar el numero de acta o tarea asociada en las observaciones del equipo cuando corresponda.",
        ]),
        p("Resultado esperado: el equipo queda actualizado, la salida de stock queda registrada, las diferencias quedan resueltas o justificadas, y la intervencion se puede reconstruir desde auditoria, tareas y actas."),
        PageBreak(),
    ])

    story += section("4. Alta de usuarios", [
        p("Inventario Modular separa autenticacion y autorizacion: Active Directory valida la identidad, pero MySQL decide que modulos puede usar cada persona."),
        p("<b>Ruta:</b> /admin/usuarios"),
        p("Hay dos tipos de usuario:"),
        info_table([
            [p("Tipo", "small"), p("Uso", "small")],
            [p("AD", "small"), p("Cuenta existente del dominio. No se guarda su clave en Inventario Modular.", "small")],
            [p("LOCAL", "small"), p("Cuenta creada dentro del sistema para laboratorio, rescate o tareas temporales. Guarda hash BCrypt, no texto plano.", "small")],
        ]),
        Spacer(1, 7),
        p("Proceso para autorizar usuario de dominio:"),
        *bullets([
            "Entrar a Usuarios.",
            "Buscar la cuenta por usuario, nombre o apellido.",
            "Seleccionar la cuenta encontrada.",
            "Asignar el rol inicial minimo necesario.",
            "Guardar autorizacion local.",
        ]),
        p("Proceso para crear usuario local:"),
        *bullets([
            "Completar usuario local, nombre visible, fuero y clave temporal.",
            "Asignar un rol limitado al trabajo que debe hacer.",
            "Desactivar o cambiar permisos cuando termina la tarea temporal.",
        ]),
    ])

    story += section("5. Stock y ordenes de armado", [
        p("El circuito de ordenes sirve para planificar armado o mejora de un equipo. Trabaja junto con Stock y el gemelo digital."),
        p("<b>Rutas:</b> /admin/stock y /admin/ordenes-armado"),
        p("Conceptos principales:"),
        info_table([
            [p("Elemento", "small"), p("Descripcion", "small")],
            [p("Stock", "small"), p("Componentes sueltos disponibles, reservados, asignados o dados de baja.", "small")],
            [p("Orden", "small"), p("Trabajo planificado sobre un equipo: armado, mejora o cambio.", "small")],
            [p("Componente esperado", "small"), p("Pieza que deberia quedar instalada segun la orden.", "small")],
            [p("Salida real", "small"), p("Confirmacion de que una pieza reservada en stock fue efectivamente asignada.", "small")],
        ]),
        Spacer(1, 7),
        p("Proceso recomendado:"),
        *bullets([
            "Cargar componentes sueltos en Stock.",
            "Entrar a Ordenes y seleccionar el equipo.",
            "Crear una orden con estado y descripcion.",
            "Agregar componentes esperados a esa orden.",
            "Reservar stock si corresponde.",
            "Cuando la pieza sale realmente del deposito, confirmar salida real desde la orden.",
            "Entrar al detalle del equipo para revisar la comparacion del gemelo digital.",
        ]),
    ])

    story += section("6. Que significa Diferencias", [
        p("<b>Diferencias</b> es el tablero que compara lo esperado contra lo detectado en el gemelo digital del equipo."),
        p("<b>Ruta:</b> /admin/dashboard-diferencias"),
        p("Sirve para responder rapido: que falta, que sobra, que coincide y que requiere revision."),
        info_table([
            [p("Estado", "small"), p("Significado", "small")],
            [p("FALTA", "small"), p("La orden o stock esperaba una pieza, pero el script/relevamiento no la detecto.", "small")],
            [p("SOBRA", "small"), p("La PC reporta una pieza que no estaba prevista como esperada.", "small")],
            [p("REVISAR", "small"), p("Hay datos parecidos, pero falta confirmar serial, modelo o capacidad.", "small")],
            [p("COINCIDE", "small"), p("Lo esperado y lo detectado coinciden segun tipo y datos fuertes.", "small")],
        ]),
        Spacer(1, 7),
        p("Uso diario: filtrar por estado, equipo o fuero; abrir el equipo afectado; revisar el detalle y corregir el dato o cerrar la accion tecnica correspondiente. La vista tambien puede exportarse como CSV desde el boton de la pantalla."),
    ])

    story += section("7. Tareas tecnicas", [
        p("El modulo <b>Tareas</b> registra trabajo operativo del equipo de Informatica. Puede asociarse a una PC o quedar como tarea general."),
        p("<b>Ruta:</b> /admin/tareas"),
        p("Proceso de uso:"),
        *bullets([
            "Crear tarea con titulo claro.",
            "Asociar equipo si corresponde.",
            "Elegir prioridad: BAJA, MEDIA, ALTA o URGENTE.",
            "Asignar responsable si ya se sabe quien la toma.",
            "Cambiar estado durante el trabajo: PENDIENTE, EN_PROCESO, CERRADA o CANCELADA.",
            "Al cerrar, dejar observaciones de cierre para auditoria operativa.",
        ]),
        p("Las tareas ayudan a no perder seguimientos que antes quedaban en mensajes, memoria personal o papel suelto."),
    ])

    story += section("8. Muebles, patrimonio y reportes", [
        p("<b>Muebles</b> registra mobiliario fisico: escritorios, sillas, mesas, racks y otros bienes de oficina."),
        p("<b>Ruta:</b> /admin/muebles"),
        p("<b>Patrimonio</b> registra bienes con numero patrimonial, custodio, ubicacion y relacion opcional con equipos."),
        p("<b>Ruta:</b> /admin/patrimonio"),
        p("<b>Reportes</b> muestra conteos operativos y exporta CSV de muebles, patrimonio y tareas."),
        p("<b>Ruta:</b> /admin/reportes"),
        *bullets([
            "En Muebles, buscar antes de cargar para evitar codigos repetidos.",
            "En Patrimonio, usar el numero patrimonial como identificador principal.",
            "En Reportes, descargar CSV solo si el usuario tiene permiso REPORTES:EXPORTAR.",
            "En Auditoria, usar filtros por usuario, modulo y accion para reconstruir quien hizo cada cambio.",
        ]),
    ])

    story += section("9. Reglas practicas de seguridad", [
        *bullets([
            "Cada persona debe usar su propio usuario.",
            "No compartir claves locales temporales.",
            "No cargar claves reales en documentos, capturas o repositorios.",
            "Si falta un modulo en el menu, revisar permisos del usuario y confirmar que el servidor este actualizado.",
            "Antes de actualizar Ubuntu con migraciones nuevas, hacer backup de MySQL.",
        ]),
    ])

    story += section("10. Comandos Ubuntu por PuTTY", [
        p("Actualizar despues de que GitLab tenga la rama principal al dia:"),
        p("""cd /opt/inventario-modular
git fetch origin
git pull --ff-only origin primeros-pasos
sh ./mvnw --batch-mode test
sh ./mvnw --batch-mode -DskipTests package
sudo systemctl restart inventario-modular.service
systemctl status inventario-modular.service --no-pager -l
curl -s http://127.0.0.1:8081/api/v1/sistema/estado""", "code"),
        p("Antes de aplicar migraciones nuevas, hacer backup de MySQL. El bloque completo esta en la bitacora del proyecto. Flujo minimo de control:"),
        p("""cd /opt/inventario-modular
git diff --name-only HEAD..origin/primeros-pasos
# Si aparecen V8__tareas_tecnicas.sql o V9__muebles_patrimonio_reportes.sql:
# 1. Ejecutar el backup documentado en la bitacora.
# 2. Confirmar que el archivo .sql.gz existe y pasa gzip -t.
# 3. Recién despues continuar con pull, build y restart.""", "code"),
    ])

    story += [
        Spacer(1, 8),
        p("Fin del manual. Este documento describe el uso operativo actual; los detalles tecnicos completos quedan en la bitacora y en el historial Git.", "small"),
    ]

    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)


if __name__ == "__main__":
    build()
