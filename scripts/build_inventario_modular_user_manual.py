from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "pdf"
OUT_FILE = OUT_DIR / "manual_usuario_inventario_modular.pdf"


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def bullets(items: list[str], styles: dict[str, ParagraphStyle]) -> ListFlowable:
    return ListFlowable(
        [ListItem(p(item, styles["Body"]), leftIndent=12) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=18,
        bulletFontName="Helvetica",
        bulletFontSize=7,
    )


def numbered(items: list[str], styles: dict[str, ParagraphStyle]) -> ListFlowable:
    return ListFlowable(
        [ListItem(p(item, styles["Body"]), leftIndent=14) for item in items],
        bulletType="1",
        leftIndent=20,
    )


def table(data: list[list[str]], widths: list[float], styles: dict[str, ParagraphStyle]) -> Table:
    rows = [[p(cell, styles["TableHead"] if row_index == 0 else styles["TableCell"]) for cell in row] for row_index, row in enumerate(data)]
    t = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E5F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B9C5CB")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFB")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F2F6F7")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return t


def code_block(text: str, styles: dict[str, ParagraphStyle]) -> Table:
    lines = text.strip("\n").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").split("\n")
    content = "<br/>".join(lines)
    t = Table([[p(content, styles["Code"])]], colWidths=[16.2 * cm], hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF3F5")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B9C5CB")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return t


def section(story: list, title: str, styles: dict[str, ParagraphStyle]) -> None:
    story.append(Spacer(1, 0.25 * cm))
    story.append(p(title, styles["Heading1"]))
    story.append(Spacer(1, 0.1 * cm))


def subsection(story: list, title: str, styles: dict[str, ParagraphStyle]) -> None:
    story.append(Spacer(1, 0.18 * cm))
    story.append(p(title, styles["Heading2"]))
    story.append(Spacer(1, 0.05 * cm))


def footer(canvas, doc) -> None:
    canvas.saveState()
    width, _ = A4
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#5D6D73"))
    canvas.drawString(2 * cm, 1.15 * cm, "Inventario Modular - Manual de Usuario")
    canvas.drawRightString(width - 2 * cm, 1.15 * cm, f"Pagina {doc.page}")
    canvas.restoreState()


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    base = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=30,
            textColor=colors.HexColor("#16333D"),
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=12,
            leading=17,
            textColor=colors.HexColor("#3B5057"),
            alignment=TA_CENTER,
        ),
        "Heading1": ParagraphStyle(
            "Heading1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#1F4E5F"),
            spaceBefore=8,
            spaceAfter=6,
        ),
        "Heading2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=15,
            textColor=colors.HexColor("#243D46"),
            spaceBefore=5,
            spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.6,
            leading=13.2,
            textColor=colors.HexColor("#1F2D33"),
            alignment=TA_LEFT,
            spaceAfter=5,
        ),
        "Small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.3,
            leading=11.2,
            textColor=colors.HexColor("#40555D"),
            spaceAfter=4,
        ),
        "Note": ParagraphStyle(
            "Note",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12.5,
            textColor=colors.HexColor("#254047"),
            backColor=colors.HexColor("#EAF4F2"),
            borderColor=colors.HexColor("#89B7AD"),
            borderWidth=0.7,
            borderPadding=7,
            spaceAfter=7,
        ),
        "Warn": ParagraphStyle(
            "Warn",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12.5,
            textColor=colors.HexColor("#4A2C00"),
            backColor=colors.HexColor("#FFF4D6"),
            borderColor=colors.HexColor("#E1B44C"),
            borderWidth=0.7,
            borderPadding=7,
            spaceAfter=7,
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.6,
            leading=11,
            textColor=colors.white,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10.5,
            textColor=colors.HexColor("#1F2D33"),
        ),
        "Code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.6,
            leading=10,
            textColor=colors.HexColor("#19323A"),
        ),
    }

    story: list = []
    story.append(Spacer(1, 2.5 * cm))
    story.append(p("Manual de Usuario", styles["Title"]))
    story.append(p("Inventario Modular", styles["Title"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(p("Centro Judicial San Pedro - Departamento de Informatica", styles["Subtitle"]))
    story.append(p("Version preparada: septiembre de 2026", styles["Subtitle"]))
    story.append(Spacer(1, 1.0 * cm))
    story.append(p("Este manual explica como ingresar, entender los permisos, administrar usuarios y resolver situaciones frecuentes del sistema Inventario Modular. Esta escrito para uso interno y evita incluir claves, tokens o secretos reales.", styles["Note"]))
    story.append(Spacer(1, 1.2 * cm))
    story.append(
        table(
            [
                ["Ambiente", "Dato de uso"],
                ["Servidor de aplicacion", "10.15.2.251"],
                ["URL directa del sistema", "http://10.15.2.251:8081"],
                ["Panel administrativo", "http://10.15.2.251:8081/admin"],
                ["Servicio Ubuntu", "inventario-modular.service"],
                ["Base de datos", "inventario_modular en MySQL 10.15.0.62"],
            ],
            [5.1 * cm, 10.9 * cm],
            styles,
        )
    )

    story.append(PageBreak())
    section(story, "1. Que es Inventario Modular", styles)
    story.append(p("Inventario Modular es el nuevo sistema Java/Spring Boot pensado para reemplazar progresivamente al inventario anterior. Su idea principal es trabajar por modulos: usuarios, roles, permisos, equipos, actas, muebles, patrimonio, stock, componentes, reportes y tareas.", styles["Body"]))
    story.append(p("La regla mas importante es simple: Active Directory confirma quien es la persona, e Inventario Modular decide que puede ver y que puede hacer dentro del sistema.", styles["Note"]))

    subsection(story, "1.1 Para quienes esta pensado", styles)
    story.append(
        bullets(
            [
                "<b>Administrador:</b> configura usuarios, roles, permisos y modulos.",
                "<b>Tecnico de Informatica:</b> consulta o trabaja sobre modulos operativos como equipos, tareas, componentes o stock, segun los permisos asignados.",
                "<b>Personal de Patrimonio:</b> consulta o administra muebles, patrimonio, componentes y reportes institucionales.",
                "<b>Lector:</b> puede mirar informacion permitida, pero no modificarla.",
                "<b>Usuario personalizado:</b> recibe una combinacion especifica de modulos y permisos.",
            ],
            styles,
        )
    )

    subsection(story, "1.2 Estado actual del sistema", styles)
    story.append(p("El sistema modular ya tiene una base productiva documentada y corre en Ubuntu por el servicio <b>inventario-modular.service</b>, en el puerto <b>8081</b>. El codigo local de esta copia contiene el proyecto base y el endpoint de salud <b>/api/v1/health</b>. En produccion se observo el panel <b>/admin</b> y la pantalla de administracion de usuarios.", styles["Body"]))
    story.append(p("Cuando una pantalla todavia no este disponible para un usuario, no significa necesariamente que el sistema fallo: puede significar que el modulo aun no fue habilitado o que ese usuario no tiene permiso.", styles["Warn"]))

    section(story, "2. Ingreso al sistema", styles)
    subsection(story, "2.1 Direccion de acceso", styles)
    story.append(p("Desde una PC conectada a la red del Centro Judicial, abrir el navegador e ingresar:", styles["Body"]))
    story.append(code_block("http://10.15.2.251:8081/admin", styles))
    story.append(p("Si se publica detras de un proxy o dominio interno en el futuro, se debe usar la direccion indicada por Informatica. El puerto directo de Spring Boot sigue siendo 8081.", styles["Small"]))

    subsection(story, "2.2 Login con usuario de dominio", styles)
    story.append(numbered([
        "Abrir la direccion del panel.",
        "Ingresar el usuario de dominio, por ejemplo <b>GMURAD</b> o el formato que indique Informatica.",
        "Ingresar la clave del dominio. El sistema no debe guardar esa clave.",
        "Presionar el boton de ingreso.",
        "Si la clave es correcta y el usuario esta autorizado en Inventario Modular, se muestran los modulos permitidos.",
    ], styles))
    story.append(p("<b>Ejemplo:</b> Maria pertenece a Patrimonio. Active Directory confirma que su usuario y clave son correctos. Inventario Modular revisa MySQL y encuentra que Maria tiene rol PATRIMONIO. Entonces Maria ve los modulos MUEBLES, PATRIMONIO, COMPONENTES y REPORTES, pero no ve la administracion completa de usuarios.", styles["Body"]))

    subsection(story, "2.3 Usuario local de emergencia", styles)
    story.append(p("En produccion se observo un usuario local de emergencia llamado <b>admin.local</b>. Este usuario sirve para recuperar acceso administrativo si Active Directory no esta disponible o si aun falta autorizar usuarios de dominio.", styles["Body"]))
    story.append(p("No dejar este usuario como unica forma permanente de administracion. Despues de ingresar, crear o autorizar el usuario real del administrador y revisar sus modulos.", styles["Warn"]))

    section(story, "3. Roles, permisos y modulos", styles)
    story.append(p("El sistema separa tres conceptos que conviene no mezclar:", styles["Body"]))
    story.append(
        table(
            [
                ["Concepto", "Que significa", "Ejemplo"],
                ["Modulo", "Area visible del sistema.", "STOCK, EQUIPOS, USUARIOS"],
                ["Rol", "Conjunto habitual de responsabilidades.", "ADMINISTRADOR, TECNICO, LECTOR"],
                ["Permiso", "Accion concreta que puede hacer el usuario.", "VER, CREAR, EDITAR, ELIMINAR"],
            ],
            [3.6 * cm, 6.5 * cm, 5.9 * cm],
            styles,
        )
    )

    subsection(story, "3.1 Roles base", styles)
    story.append(
        table(
            [
                ["Rol", "Uso recomendado"],
                ["ADMINISTRADOR", "Acceso total. Debe quedar reservado para responsables del sistema."],
                ["TECNICO", "Trabajo operativo en equipos, tareas, componentes y stock, segun necesidad."],
                ["PATRIMONIO", "Gestion o consulta de muebles, patrimonio, componentes y reportes."],
                ["LECTOR", "Consulta sin cambios. Ideal para usuarios que solo necesitan verificar datos."],
                ["PERSONALIZADO", "Casos especiales donde el usuario necesita una combinacion puntual."],
            ],
            [4.1 * cm, 11.9 * cm],
            styles,
        )
    )

    subsection(story, "3.2 Permisos base", styles)
    story.append(
        table(
            [
                ["Permiso", "Permite"],
                ["VER", "Consultar listados, detalles y pantallas del modulo."],
                ["CREAR", "Registrar nuevos elementos."],
                ["EDITAR", "Modificar informacion existente."],
                ["ELIMINAR", "Borrar o desactivar informacion, si el modulo lo permite."],
                ["EXPORTAR", "Generar archivos, planillas o reportes."],
                ["ADMINISTRAR", "Configurar reglas, catalogos o permisos del modulo."],
            ],
            [4.1 * cm, 11.9 * cm],
            styles,
        )
    )

    subsection(story, "3.3 Ejemplos claros de permisos", styles)
    story.append(
        bullets(
            [
                "Un usuario con <b>VER</b> en STOCK puede consultar existencias, pero no cargar un remito.",
                "Un usuario con <b>CREAR</b> en ACTAS puede generar un acta nueva si el modulo esta disponible.",
                "Un usuario con <b>EDITAR</b> en EQUIPOS puede corregir datos de una PC ya registrada.",
                "Un usuario con <b>EXPORTAR</b> en REPORTES puede descargar informacion para control interno.",
                "Un usuario sin permiso para USUARIOS no debe ver la administracion de cuentas aunque conozca la URL.",
            ],
            styles,
        )
    )

    section(story, "4. Administracion de usuarios", styles)
    story.append(p("La administracion de usuarios es la pantalla clave del sistema modular. Desde ahi el administrador autoriza personas, asigna roles y define que modulos puede usar cada una.", styles["Body"]))
    story.append(p("Importante: un usuario puede existir en Active Directory y aun asi no tener acceso al sistema. Primero debe estar autorizado localmente en Inventario Modular.", styles["Note"]))

    subsection(story, "4.1 Autorizar un usuario de dominio", styles)
    story.append(numbered([
        "Ingresar con un usuario administrador.",
        "Abrir <b>Administracion de usuarios</b>.",
        "Buscar el usuario de dominio por nombre, apellido o username. Ejemplo: <b>GMURAD</b>.",
        "Seleccionar el usuario correcto.",
        "Elegir un rol inicial: por ejemplo TECNICO, PATRIMONIO o LECTOR.",
        "Marcar los modulos que debe ver.",
        "Guardar los cambios.",
        "Pedir al usuario que cierre sesion y vuelva a ingresar.",
    ], styles))
    story.append(p("<b>Ejemplo:</b> Juan Perez es tecnico. Se lo busca como <b>JPEREZ</b>, se lo autoriza con rol TECNICO y se habilitan EQUIPOS, TAREAS y STOCK. Cuando Juan entra, no deberia ver USUARIOS ni PATRIMONIO si no fueron habilitados.", styles["Body"]))

    subsection(story, "4.2 Asignar modulos a un usuario que ya entra pero no ve nada", styles)
    story.append(numbered([
        "Confirmar que el usuario puede iniciar sesion.",
        "Entrar como administrador.",
        "Abrir la ficha del usuario en Usuarios autorizados.",
        "Revisar si esta activo.",
        "Agregar rol o modulos faltantes.",
        "Guardar.",
        "Pedir al usuario que vuelva a iniciar sesion.",
    ], styles))
    story.append(p("<b>Caso comun:</b> el usuario de dominio valida bien contra AD, pero queda sin modulos. La causa no suele ser la clave: suele faltar autorizacion local o asignacion de modulos.", styles["Note"]))

    subsection(story, "4.3 Desactivar un usuario", styles)
    story.append(p("Cuando una persona deja de usar el sistema, conviene desactivarla en lugar de borrar su historial. Asi se conserva la trazabilidad de acciones pasadas.", styles["Body"]))
    story.append(numbered([
        "Entrar como administrador.",
        "Buscar el usuario en Usuarios autorizados.",
        "Cambiar su estado a inactivo o deshabilitado.",
        "Guardar.",
        "Verificar que el usuario ya no pueda ingresar.",
    ], styles))

    subsection(story, "4.4 Buenas practicas de administracion", styles)
    story.append(bullets([
        "Dar ADMINISTRADOR solo a quienes realmente administran el sistema.",
        "Preferir LECTOR para usuarios que solo necesitan consultar.",
        "Separar PATRIMONIO y TECNICO cuando las responsabilidades sean distintas.",
        "Revisar permisos despues de cambios de puesto o dependencia.",
        "No compartir usuarios. Cada persona debe entrar con su propia cuenta.",
    ], styles))

    section(story, "5. Modulos del sistema", styles)
    story.append(p("Inventario Modular esta pensado para crecer por partes. Un modulo puede aparecer, ocultarse o quedar sin acceso segun el estado de desarrollo y los permisos del usuario.", styles["Body"]))
    story.append(
        table(
            [
                ["Modulo", "Para que sirve", "Ejemplo de uso"],
                ["EQUIPOS", "Administrar computadoras y equipamiento informatico.", "Consultar una PC por nombre, fuero o usuario asignado."],
                ["ACTAS", "Gestionar actas asociadas a entregas, movimientos o intervenciones.", "Crear un acta de entrega de equipo."],
                ["MUEBLES", "Registrar bienes muebles de uso operativo.", "Consultar sillas, escritorios o armarios por oficina."],
                ["PATRIMONIO", "Control institucional y numeracion patrimonial.", "Ver bienes con numero patrimonial y generar reporte."],
                ["STOCK", "Controlar insumos y existencias.", "Cargar ingreso por remito y consultar cantidades disponibles."],
                ["COMPONENTES", "Administrar partes o repuestos.", "Registrar memoria, disco o fuente usados en una reparacion."],
                ["USUARIOS", "Administrar acceso, roles y permisos.", "Autorizar un usuario de dominio."],
                ["REPORTES", "Consultar informacion consolidada.", "Exportar listado por modulo o dependencia."],
                ["TAREAS", "Gestionar trabajos o pedidos tecnicos.", "Registrar seguimiento de una intervencion."],
            ],
            [3.0 * cm, 6.2 * cm, 6.8 * cm],
            styles,
        )
    )

    subsection(story, "5.1 Que hacer si falta un modulo", styles)
    story.append(numbered([
        "Confirmar con otro usuario administrador si el modulo existe en esa version.",
        "Revisar si el usuario tiene el rol correcto.",
        "Revisar si el modulo esta marcado como visible para ese usuario o rol.",
        "Cerrar sesion y volver a entrar.",
        "Si sigue sin aparecer, revisar logs o consultar a Informatica.",
    ], styles))

    story.append(PageBreak())
    section(story, "6. Casos de uso operativos", styles)
    story.append(p("Los siguientes casos explican como deberia trabajarse en el sistema cuando los modulos EQUIPOS, COMPONENTES, STOCK y ACTAS esten disponibles para el usuario. Sirven como guia practica para cargar informacion de forma ordenada y trazable.", styles["Body"]))
    story.append(p("Regla general: primero se registra el dato principal, despues se relacionan componentes, usuario, ubicacion y documentacion. Evitar crear registros duplicados si el elemento ya existe.", styles["Note"]))

    subsection(story, "6.1 Caso de uso: ingresa una PC nueva", styles)
    story.append(p("<b>Situacion:</b> llega una computadora nueva al Departamento de Informatica y hay que incorporarla al inventario.", styles["Body"]))
    story.append(numbered([
        "Entrar al sistema con un usuario que tenga permiso CREAR en EQUIPOS.",
        "Abrir el modulo <b>EQUIPOS</b>.",
        "Elegir <b>Nuevo equipo</b> o la accion equivalente.",
        "Cargar el nombre interno de la PC. Ejemplo: <b>SP-INF-023</b>.",
        "Completar tipo, marca, modelo, numero de serie y numero patrimonial si corresponde.",
        "Indicar estado inicial. Ejemplo: <b>Disponible</b>, <b>En preparacion</b> o <b>Asignada</b>.",
        "Registrar ubicacion o dependencia. Ejemplo: <b>Informatica - Taller</b>.",
        "Si ya tiene destino, vincular usuario o sector responsable.",
        "Guardar el equipo.",
        "Verificar que aparezca en el listado y que pueda buscarse por nombre, serie o patrimonio.",
    ], styles))
    story.append(p("<b>Ejemplo completo:</b> se recibe una PC Dell OptiPlex con serie ABC123. Se registra como SP-INF-023, estado En preparacion, ubicacion Informatica - Taller, sin usuario asignado todavia. Cuando se entregue, se actualiza el estado a Asignada y se vincula a la oficina o usuario final.", styles["Body"]))

    subsection(story, "6.2 Caso de uso: se registra una PC usada que ya estaba en servicio", styles)
    story.append(p("<b>Situacion:</b> se detecta una PC que ya esta instalada en una oficina, pero no aparece en Inventario Modular.", styles["Body"]))
    story.append(numbered([
        "Buscar primero por nombre de equipo, numero de serie y numero patrimonial.",
        "Si no aparece, abrir <b>Nuevo equipo</b>.",
        "Cargar los datos visibles sin inventar informacion faltante.",
        "Marcar el estado como <b>En uso</b> o <b>Asignada</b>.",
        "Registrar la oficina, fuero o dependencia donde se encontro.",
        "Vincular el usuario responsable si se conoce.",
        "Agregar una observacion. Ejemplo: <b>Equipo relevado en oficina, pendiente validar serie interna</b>.",
        "Guardar y avisar si falta completar algun dato patrimonial.",
    ], styles))
    story.append(p("<b>Buen criterio:</b> si falta el numero de serie, no duplicar el registro despues. Actualizar el mismo equipo cuando el dato aparezca.", styles["Warn"]))

    subsection(story, "6.3 Caso de uso: entra un componente nuevo a stock", styles)
    story.append(p("<b>Situacion:</b> llega un lote de discos, memorias, fuentes u otros repuestos y hay que cargarlos para que queden disponibles.", styles["Body"]))
    story.append(numbered([
        "Entrar con permiso CREAR en STOCK o COMPONENTES.",
        "Abrir <b>STOCK</b> si se carga un ingreso por cantidad, o <b>COMPONENTES</b> si se identifica cada pieza individualmente.",
        "Registrar tipo de componente. Ejemplo: <b>SSD 480 GB</b>, <b>Memoria DDR4 8 GB</b>, <b>Fuente ATX</b>.",
        "Cargar marca, modelo, numero de serie si existe y cantidad recibida.",
        "Indicar origen. Ejemplo: compra, remito, recuperado de baja, donacion interna.",
        "Guardar el ingreso.",
        "Verificar que el componente quede con estado <b>Disponible</b>.",
    ], styles))
    story.append(p("<b>Ejemplo:</b> llega un remito con 10 SSD Kingston 480 GB. Se carga un ingreso de stock con cantidad 10, origen Remito, y quedan disponibles para futuras reparaciones o armado de equipos.", styles["Body"]))

    subsection(story, "6.4 Caso de uso: se recupera un componente usado", styles)
    story.append(p("<b>Situacion:</b> una PC se da de baja o se desarma, pero algunos componentes sirven para reutilizar.", styles["Body"]))
    story.append(numbered([
        "Abrir la ficha del equipo de origen si existe.",
        "Registrar el retiro del componente. Ejemplo: memoria DDR3 4 GB o disco SATA 500 GB.",
        "Cargar el componente en COMPONENTES con estado <b>Usado disponible</b> o equivalente.",
        "Indicar origen: equipo del que fue retirado.",
        "Agregar observacion de estado fisico. Ejemplo: <b>Probado, funciona correctamente</b>.",
        "Guardar.",
        "Si el componente no funciona, registrarlo como <b>No reutilizable</b> o derivarlo a baja, segun la regla vigente.",
    ], styles))
    story.append(p("<b>Ejemplo:</b> se retira una memoria de una PC dada de baja. Se registra como componente usado, origen SP-ADM-011, estado Probado. Luego puede usarse para reparar otra PC y queda trazado de donde salio.", styles["Body"]))

    subsection(story, "6.5 Caso de uso: armar un equipo nuevo con componentes", styles)
    story.append(p("<b>Situacion:</b> Informatica arma una PC usando gabinete, disco, memoria y otros componentes disponibles.", styles["Body"]))
    story.append(numbered([
        "Verificar que todos los componentes existan en STOCK o COMPONENTES.",
        "Crear la ficha del nuevo equipo en EQUIPOS.",
        "Asignar nombre interno. Ejemplo: <b>SP-TALLER-005</b>.",
        "Relacionar cada componente usado con el equipo nuevo.",
        "Cambiar el estado de esos componentes a <b>Instalado</b> o <b>Asignado a equipo</b>.",
        "Completar ubicacion inicial y responsable si ya se conoce.",
        "Agregar observacion tecnica. Ejemplo: <b>Equipo armado con SSD nuevo y memoria recuperada</b>.",
        "Guardar.",
        "Revisar la ficha final: debe mostrar equipo, componentes vinculados, estado y ubicacion.",
    ], styles))
    story.append(p("<b>Ejemplo completo:</b> se arma SP-TALLER-005 con un SSD nuevo de stock, una memoria usada recuperada y una fuente nueva. El sistema debe descontar o marcar esos componentes como utilizados, y la ficha del equipo debe mostrar la composicion real.", styles["Body"]))

    subsection(story, "6.6 Caso de uso: reemplazar un componente en una PC existente", styles)
    story.append(p("<b>Situacion:</b> una PC falla y se cambia el disco o la memoria.", styles["Body"]))
    story.append(numbered([
        "Buscar la PC en EQUIPOS.",
        "Abrir su ficha.",
        "Registrar el componente que se retira y su estado. Ejemplo: <b>Disco con falla</b>.",
        "Seleccionar el componente nuevo o usado que se instala.",
        "Guardar el cambio.",
        "Agregar observacion de intervencion: fecha, motivo y tecnico.",
        "Si corresponde, generar o vincular un acta o tarea.",
    ], styles))
    story.append(p("<b>Ejemplo:</b> a la PC SP-MP-014 se le cambia un HDD fallado por un SSD 480 GB. El HDD queda como No reutilizable y el SSD queda vinculado a SP-MP-014.", styles["Body"]))

    subsection(story, "6.7 Caso de uso: entregar una PC a una oficina", styles)
    story.append(p("<b>Situacion:</b> un equipo ya preparado se entrega a una dependencia o usuario final.", styles["Body"]))
    story.append(numbered([
        "Abrir la ficha del equipo.",
        "Confirmar que los datos tecnicos y patrimoniales esten completos.",
        "Cambiar estado a <b>Asignada</b> o <b>En uso</b>.",
        "Cargar dependencia, oficina, fuero o usuario responsable.",
        "Generar acta de entrega si el modulo ACTAS esta disponible.",
        "Guardar.",
        "Verificar que el equipo ya no figure como disponible en stock operativo.",
    ], styles))
    story.append(p("<b>Ejemplo:</b> SP-INF-023 se entrega a Mesa de Entradas. Se asigna a la oficina correspondiente, se genera el acta de entrega y queda registrada la trazabilidad del movimiento.", styles["Body"]))

    story.append(PageBreak())
    section(story, "7. Ejemplos por perfil", styles)
    subsection(story, "7.1 Administrador", styles)
    story.append(p("<b>Situacion:</b> entra una nueva persona a Informatica y necesita usar tareas y equipos.", styles["Body"]))
    story.append(numbered([
        "Ingresar a /admin.",
        "Abrir Administracion de usuarios.",
        "Buscar el usuario de dominio.",
        "Asignar rol TECNICO.",
        "Habilitar EQUIPOS y TAREAS.",
        "Guardar.",
        "Pedir a la persona que ingrese con su usuario de dominio.",
    ], styles))

    subsection(story, "7.2 Tecnico", styles)
    story.append(p("<b>Situacion:</b> el tecnico necesita trabajar con stock, pero no ve el modulo.", styles["Body"]))
    story.append(numbered([
        "Confirmar que ingreso con su usuario propio.",
        "Cerrar sesion y volver a entrar por si hubo un cambio reciente de permisos.",
        "Si el modulo sigue sin aparecer, pedir al administrador que revise si tiene STOCK habilitado.",
        "No intentar entrar por URL directa: si no tiene permiso, el sistema debe responder 403 o bloquear el acceso.",
    ], styles))

    subsection(story, "7.3 Patrimonio", styles)
    story.append(p("<b>Situacion:</b> una persona de patrimonio necesita consultar bienes y exportar un listado.", styles["Body"]))
    story.append(numbered([
        "Ingresar al sistema.",
        "Abrir PATRIMONIO o REPORTES, segun el permiso asignado.",
        "Filtrar por dependencia, oficina o numero patrimonial cuando el modulo este disponible.",
        "Usar EXPORTAR solo si el permiso fue otorgado.",
    ], styles))

    subsection(story, "7.4 Lector", styles)
    story.append(p("<b>Situacion:</b> un jefe necesita mirar informacion pero no modificarla.", styles["Body"]))
    story.append(p("Asignar rol LECTOR y solo los modulos necesarios. Si intenta crear, editar o eliminar, el sistema debe impedirlo.", styles["Body"]))

    story.append(PageBreak())
    section(story, "8. Mensajes y problemas frecuentes", styles)
    story.append(
        table(
            [
                ["Situacion", "Causa probable", "Que hacer"],
                ["Usuario o clave incorrectos", "Active Directory rechazo la autenticacion.", "Verificar usuario, teclado, mayusculas y clave de dominio."],
                ["Entra pero no ve modulos", "Falta autorizacion local o modulos asignados.", "Administrador debe revisar Usuarios autorizados."],
                ["No autorizado o 403", "El usuario no tiene permiso para esa accion o URL.", "Pedir permiso especifico; no es error de navegador."],
                ["No se pudo consultar Active Directory", "LDAP/AD no disponible o busqueda no configurada.", "Ingresar con admin local y revisar configuracion/logs."],
                ["Pantalla en blanco o no carga", "Servicio caido, deploy incompleto o error de servidor.", "Informar a Informatica y revisar servicio/logs."],
                ["Health responde ok pero /admin falla", "La app base esta viva, pero fallo una parte de seguridad o admin.", "Revisar logs de inventario-modular.service."],
            ],
            [4.5 * cm, 5.8 * cm, 5.7 * cm],
            styles,
        )
    )

    subsection(story, "8.1 Verificacion rapida de disponibilidad", styles)
    story.append(p("Para usuarios finales, la verificacion simple es abrir el panel en el navegador. Para administradores tecnicos, el endpoint de salud debe responder con estado ok:", styles["Body"]))
    story.append(code_block("http://10.15.2.251:8081/api/v1/health", styles))
    story.append(p("Respuesta esperada aproximada:", styles["Body"]))
    story.append(code_block('{"status":"ok","service":"inventario-modular","timestamp":"..."}', styles))

    section(story, "9. Reglas de seguridad para usuarios", styles)
    story.append(bullets([
        "No compartir usuario ni clave de dominio.",
        "No pedir permisos de ADMINISTRADOR si solo hace falta consultar.",
        "No copiar capturas con datos sensibles fuera del ambito laboral.",
        "Avisar si aparece informacion de modulos que no corresponden a su funcion.",
        "Cerrar sesion al terminar en equipos compartidos.",
        "Reportar errores con fecha, hora, usuario, pantalla y accion realizada.",
    ], styles))

    section(story, "10. Anexo para administradores tecnicos", styles)
    story.append(p("Esta seccion no es necesaria para el usuario comun, pero ayuda al responsable del sistema a diagnosticar problemas sin exponer secretos.", styles["Body"]))

    subsection(story, "10.1 Comandos de estado en Ubuntu", styles)
    story.append(code_block(
        """
sudo systemctl status inventario-modular --no-pager -l
sudo journalctl -u inventario-modular -n 120 --no-pager
curl -I http://127.0.0.1:8081 || true
curl -I http://10.15.2.251:8081 || true
        """,
        styles,
    ))

    subsection(story, "10.2 Revisar variables sin mostrar claves", styles)
    story.append(code_block(
        """
sudo grep -Ei "LDAP|AD_|DOMAIN|BASE_DN|READ_ONLY|INVENTARIO_DB_URL|INVENTARIO_DB_USER" \\
  /etc/inventario-modular/inventario-modular.env
        """,
        styles,
    ))

    subsection(story, "10.3 Backup antes de migraciones", styles)
    story.append(p("Si una actualizacion incluye migraciones Flyway, hacer backup antes de reiniciar. El usuario de aplicacion tiene permisos limitados, por eso el dump debe usar opciones compatibles.", styles["Body"]))
    story.append(code_block(
        """
mysqldump --single-transaction --skip-lock-tables --no-tablespaces \\
  -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" | gzip > "$BACKUP"
gzip -t "$BACKUP"
ls -lh "$BACKUP"
        """,
        styles,
    ))

    subsection(story, "10.4 Lo que no se debe hacer", styles)
    story.append(bullets([
        "No usar /opt/inventario para Inventario Modular.",
        "No correr deploy_ubuntu.sh para este sistema; ese script pertenece al Flask legado.",
        "No reiniciar inventario.service para cambios del modular.",
        "No documentar claves reales en archivos del repositorio.",
        "No considerar valido un backup si mysqldump fallo o si el archivo resultante pesa unos pocos bytes.",
    ], styles))

    section(story, "11. Como reportar un problema", styles)
    story.append(p("Cuando algo falle, enviar un reporte corto pero completo. Esto acelera mucho la resolucion.", styles["Body"]))
    story.append(
        table(
            [
                ["Dato", "Ejemplo"],
                ["Usuario", "GMURAD"],
                ["Fecha y hora", "02/09/2026 09:40"],
                ["Pantalla", "Administracion de usuarios"],
                ["Accion", "Intente guardar modulos para JPEREZ"],
                ["Resultado", "El sistema mostro No autorizado"],
                ["Captura", "Adjuntar solo si no expone informacion sensible"],
            ],
            [4.2 * cm, 11.8 * cm],
            styles,
        )
    )

    story.append(Spacer(1, 0.35 * cm))
    story.append(p("Cierre: Inventario Modular debe crecer de forma controlada. Si un usuario no ve un modulo, primero se revisan permisos. Si el sistema no responde, se revisa el servicio. Si Active Directory autentica pero el usuario queda sin acceso, se autoriza localmente en el panel.", styles["Note"]))

    doc = SimpleDocTemplate(
        str(OUT_FILE),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.7 * cm,
        bottomMargin=1.8 * cm,
        title="Manual de Usuario - Inventario Modular",
        author="Departamento de Informatica - Centro Judicial San Pedro",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUT_FILE)


if __name__ == "__main__":
    build()
