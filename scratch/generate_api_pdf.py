import os
from fpdf import FPDF, XPos, YPos

class PDFReport(FPDF):
    def header(self):
        self.set_fill_color(15, 32, 67) # Azul oscuro institucional
        self.rect(0, 0, 210, 16, 'F')
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.cell(110, 8, "PODER JUDICIAL DE JUJUY - CENTRO JUDICIAL SAN PEDRO", align="L")
        self.set_font("Helvetica", "", 9)
        self.cell(80, 8, "Departamento de Informatica", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Documento Tecnico de Integracion API Contable - Pagina {self.page_no()}/{{nb}}", align="C")

def create_api_documentation_pdf(output_path):
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Título Principal
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(15, 32, 67)
    pdf.cell(0, 8, "Manual de Integracion API REST - Sistema Contable", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(70, 80, 95)
    pdf.cell(0, 5, "Especificacion de Endpoints, Ejemplos JSON y Guia de Pruebas en Postman", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    
    pdf.set_draw_color(15, 32, 67)
    pdf.set_line_width(0.8)
    pdf.line(10, 36, 200, 36)
    pdf.ln(5)

    # Bloque de Resumen de Conexión
    pdf.set_fill_color(240, 244, 248)
    pdf.set_draw_color(200, 215, 230)
    pdf.rect(10, 40, 190, 42, 'DF')
    
    pdf.set_xy(14, 43)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 32, 67)
    pdf.cell(0, 5, "DATOS DE CONEXION Y AUTENTICACION EN PRODUCCION", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 30, 30)
    pdf.set_x(14)
    pdf.cell(48, 5, "URL Base Produccion:")
    pdf.set_font("Courier", "B", 9)
    pdf.cell(0, 5, "https://10.15.2.251:5000", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(14)
    pdf.cell(48, 5, "Metodo de Autenticacion:")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Bearer Token (Cabecera 'Authorization: Bearer <TOKEN>')", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(14)
    pdf.cell(48, 5, "Token Oficial de Produccion:")
    pdf.set_font("Courier", "B", 9)
    pdf.set_text_color(180, 40, 40)
    pdf.cell(0, 5, "z-NFJcr4BpXUypVxruNth3sBUSYelf8TKDTsB8cm4N0", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(80, 80, 80)
    pdf.set_x(14)
    pdf.cell(0, 5, "* Nota SSL: El servidor utiliza certificado HTTPS interno. Desactivar 'SSL Certificate Verification' en Postman.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_y(88)

    # Sección 1: Seguridad y Headers
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 32, 67)
    pdf.cell(0, 7, "1. Cabeceras HTTP Requeridas", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 4.5, "Todas las peticiones enviadas a la API deben incluir obligatoriamente la cabecera HTTP 'Authorization' utilizando el esquema Bearer. Si el token no esta presente o es invalido, el servidor rechazara la solicitud con HTTP 401 Unauthorized.")
    pdf.ln(3)

    # Tabla de Headers
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_fill_color(220, 230, 242)
    pdf.cell(45, 6, "Cabecera (Header)", 1, 0, 'C', True)
    pdf.cell(85, 6, "Valor Requerido", 1, 0, 'C', True)
    pdf.cell(60, 6, "Descripcion", 1, 1, 'C', True)
    
    pdf.set_font("Courier", "", 8)
    pdf.cell(45, 5.5, "Authorization", 1, 0, 'L')
    pdf.cell(85, 5.5, "Bearer z-NFJcr4BpXUypVxruNth3sBUSY...", 1, 0, 'L')
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(60, 5.5, "Token de acceso a la API Contable", 1, 1, 'L')
    
    pdf.set_font("Courier", "", 8)
    pdf.cell(45, 5.5, "Accept", 1, 0, 'L')
    pdf.cell(85, 5.5, "application/json", 1, 0, 'L')
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(60, 5.5, "Formato de respuesta JSON UTF-8", 1, 1, 'L')

    pdf.ln(5)

    # Sección 2: Endpoints
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 32, 67)
    pdf.cell(0, 7, "2. Catalogo de Endpoints de Consulta", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Endpoint 1
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(15, 5, "GET", 0, 0, 'L')
    pdf.set_text_color(15, 32, 67)
    pdf.cell(0, 5, "/api/external/purchase-orders (Listado / Barrido Paginado)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 4, "Obtiene la lista de Ordenes de Compra en inventario. Admite filtros opcionales: since (YYYY-MM-DD), until (YYYY-MM-DD), page (def: 1), per_page (def: 50, max: 200).")
    pdf.ln(2)

    # Code block JSON 1
    json_1 = """GET https://10.15.2.251:5000/api/external/purchase-orders?since=2026-07-01&until=2026-07-31

Respuesta HTTP 200 OK:
{
  "status": "success",
  "page": 1,
  "per_page": 50,
  "total_purchase_orders": 1,
  "total_pages": 1,
  "purchase_orders": [
    {
      "oc_number": "185-2026",
      "last_received_at": "2026-07-30",
      "total_items": 90,
      "remitos_count": 1
    }
  ]
}"""
    pdf.set_font("Courier", "", 8)
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(210, 215, 220)
    pdf.rect(10, pdf.get_y(), 190, 48, 'DF')
    pdf.set_x(12)
    pdf.multi_cell(186, 3.6, json_1)
    pdf.set_y(pdf.get_y() + 4)

    # Nueva página para Endpoint 2, 3 y Postman
    pdf.add_page()

    # Endpoint 2
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(15, 5, "GET", 0, 0, 'L')
    pdf.set_text_color(15, 32, 67)
    pdf.cell(0, 5, "/api/external/purchase-orders/{oc_number} (Detalle Completo de OC)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 4, "Recupera los datos de una Orden de Compra especifica, agrupando remitos recibidos, tipos de componentes, marcas/modelos, cantidades y numeros de serie fisicos.")
    pdf.ln(2)

    json_2 = """GET https://10.15.2.251:5000/api/external/purchase-orders/185-2026

Respuesta HTTP 200 OK:
{
  "status": "success",
  "oc_number": "185-2026",
  "total_items": 90,
  "total_remitos": 1,
  "remitos": [
    {
      "invoice_number": "REM-00871",
      "supplier": "Insumos Jujuy SRL",
      "received_at": "2026-07-30",
      "items": [
        {
          "component_type": "Monitor",
          "brand_model": "Dell P2422H 24 pulgadas",
          "quantity": 10,
          "serials": ["ZA12606000514", "ZA12606000515", "..."]
        }
      ]
    }
  ]
}"""
    pdf.set_font("Courier", "", 8)
    pdf.set_fill_color(245, 247, 250)
    pdf.rect(10, pdf.get_y(), 190, 54, 'DF')
    pdf.set_x(12)
    pdf.multi_cell(186, 3.6, json_2)
    pdf.set_y(pdf.get_y() + 5)

    # Endpoint 3
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(15, 5, "GET", 0, 0, 'L')
    pdf.set_text_color(15, 32, 67)
    pdf.cell(0, 5, "/api/external/remitos/{invoice_number} (Consulta por Remito)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 4, "Permite consultar directamente un numero de remito para conciliar la entrega fisica con el proveedor.")
    pdf.ln(2)

    json_3 = """GET https://10.15.2.251:5000/api/external/remitos/REM-00871

Respuesta HTTP 200 OK:
{
  "status": "success",
  "invoice_number": "REM-00871",
  "oc_number": "185-2026",
  "supplier": "Insumos Jujuy SRL",
  "received_at": "2026-07-30",
  "total_items": 90,
  "items": [ ... ]
}"""
    pdf.set_font("Courier", "", 8)
    pdf.set_fill_color(245, 247, 250)
    pdf.rect(10, pdf.get_y(), 190, 36, 'DF')
    pdf.set_x(12)
    pdf.multi_cell(186, 3.6, json_3)
    pdf.set_y(pdf.get_y() + 5)

    # Sección 3: Guía de Pruebas en Postman
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 32, 67)
    pdf.cell(0, 7, "3. Pasos para Configurar y Probar en Postman", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(40, 40, 40)
    steps = [
        "1. Desactivar SSL: En Postman -> Settings (engranaje) -> General -> Cambiar 'SSL certificate verification' a OFF.",
        "2. Crear Peticion HTTP GET con la URL (ej: https://10.15.2.251:5000/api/external/purchase-orders/185-2026).",
        "3. Ir a la pestana 'Authorization', seleccionar Type: 'Bearer Token'.",
        "4. En el campo Token pegar la clave oficial: z-NFJcr4BpXUypVxruNth3sBUSYelf8TKDTsB8cm4N0",
        "5. Presionar 'Send'. Debera retornar HTTP 200 OK con el cuerpo JSON."
    ]
    for step in steps:
        pdf.set_x(12)
        pdf.cell(0, 4.5, step, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(3)

    # Sección 4: Códigos de Estado HTTP
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 32, 67)
    pdf.cell(0, 7, "4. Codigos de Respuesta HTTP y Errores", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(220, 230, 242)
    pdf.cell(25, 5.5, "Codigo HTTP", 1, 0, 'C', True)
    pdf.cell(40, 5.5, "Estado", 1, 0, 'C', True)
    pdf.cell(125, 5.5, "Significado / Causa", 1, 1, 'C', True)

    pdf.set_font("Helvetica", "", 8)
    codes = [
        ("200 OK", "Exito", "La consulta fue procesada correctamente y retorna los datos en JSON."),
        ("400 Bad Request", "Error de Peticion", "Parametro invalido o envio de peticion HTTP plano a puerto HTTPS."),
        ("401 Unauthorized", "No Autorizado", "El Bearer Token falta o no coincide con el token oficial."),
        ("404 Not Found", "No Encontrado", "La Orden de Compra o Remito especificado no existe en inventario."),
        ("429 Too Many Requests", "Limite Excedido", "Se supero el limite de seguridad de 60 peticiones por minuto."),
        ("500 Internal Error", "Error Servidor", "Error interno o problema de conexion con la base de datos MySQL.")
    ]
    for code, status, desc in codes:
        pdf.set_x(10)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(25, 5, code, 1, 0, 'C')
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(40, 5, status, 1, 0, 'L')
        pdf.cell(125, 5, desc, 1, 1, 'L')

    pdf.output(output_path)
    print(f"PDF generado exitosamente en: {output_path}")

if __name__ == "__main__":
    out = os.path.join(os.getcwd(), "Especificacion_API_Contable_Postman.pdf")
    create_api_documentation_pdf(out)
