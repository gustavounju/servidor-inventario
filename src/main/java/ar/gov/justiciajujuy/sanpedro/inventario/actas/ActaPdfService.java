package ar.gov.justiciajujuy.sanpedro.inventario.actas;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import org.springframework.stereotype.Service;
import org.thymeleaf.context.Context;
import org.thymeleaf.spring6.SpringTemplateEngine;
import org.xhtmlrenderer.pdf.ITextRenderer;

/**
 * Servicio para la generación de actas oficiales e institucionales en formato PDF.
 * <p>
 * Utiliza <b>Flying Saucer (OpenPDF)</b> acoplado al motor de plantillas <b>Thymeleaf</b>
 * para procesar una plantilla XHTML institucional ({@code pdf/acta-institucional.html})
 * con membrete del <i>Poder Judicial de Jujuy - Centro Judicial San Pedro</i>.
 * <p>
 * Características del circuito:
 * <ul>
 *   <li>Inyección del modelo de datos del acta y equipo asociado para enriquecer la ficha técnica.</li>
 *   <li>Cumplimiento estricto del estándar XHTML/CSS para renderizado fiel y paginado A4.</li>
 *   <li>Mecanismo de resguardo (fallback) a bajo nivel en caso de contingencia o fallo de parseo XML.</li>
 * </ul>
 */
@Service
public class ActaPdfService {

	private static final DateTimeFormatter FECHA = DateTimeFormatter.ofPattern("dd/MM/yyyy");

	private final SpringTemplateEngine templateEngine;
	private final EquipoRepository equipoRepository;

	public ActaPdfService(SpringTemplateEngine templateEngine, EquipoRepository equipoRepository) {
		this.templateEngine = templateEngine;
		this.equipoRepository = equipoRepository;
	}

	/**
	 * Genera el documento PDF formal correspondiente a un acta institucional.
	 *
	 * @param acta detalle de la información del acta (número, tipo, estado, intervinientes, detalles)
	 * @return arreglo de bytes con el contenido binario del archivo PDF generado
	 */
	public byte[] generar(ActaService.ActaDetalle acta) {
		try {
			// 1. Preparar el contexto de variables para Thymeleaf
			Context context = new Context();
			context.setVariable("acta", acta);

			// 2. Enriquecer con los datos de hardware del equipo vinculado si existe
			if (acta.equipoId() != null) {
				equipoRepository.findById(acta.equipoId()).ifPresent(equipo -> context.setVariable("equipo", equipo));
			}

			// 3. Renderizar la plantilla XHTML institucional
			String html = templateEngine.process("pdf/acta-institucional", context);

			// 4. Transformar el documento XHTML en PDF mediante Flying Saucer
			try (ByteArrayOutputStream os = new ByteArrayOutputStream()) {
				ITextRenderer renderer = new ITextRenderer();
				renderer.setDocumentFromString(html);
				renderer.layout();
				renderer.createPDF(os);
				return os.toByteArray();
			}
		} catch (Exception ex) {
			// 5. En caso de imprevisto, recurrir a la generación directa de bajo nivel
			return fallbackPdf(acta);
		}
	}

	private byte[] fallbackPdf(ActaService.ActaDetalle acta) {
		List<String> lineas = new ArrayList<>();
		lineas.add("Poder Judicial de Jujuy - Centro Judicial San Pedro");
		lineas.add("Inventario Modular");
		lineas.add("");
		lineas.add("ACTA " + texto(acta.numero()));
		lineas.add("");
		lineas.add("Tipo: " + texto(acta.tipo()));
		lineas.add("Estado: " + texto(acta.estado()));
		lineas.add("Fecha de emision: " + (acta.fechaEmision() == null ? "Sin fecha" : FECHA.format(acta.fechaEmision())));
		lineas.add("Equipo: " + texto(acta.equipoNombre(), "Sin equipo"));
		lineas.add("Destinatario: " + texto(acta.destinatario()));
		lineas.add("Responsable de entrega: " + texto(acta.responsableEntrega(), "Sin informar"));
		lineas.add("Responsable de recepcion: " + texto(acta.responsableRecepcion(), "Sin informar"));
		lineas.add("");
		lineas.add("Detalle:");
		lineas.addAll(partir(texto(acta.detalle()), 92));
		lineas.add("");
		lineas.add("Observaciones:");
		lineas.addAll(partir(texto(acta.observaciones(), "Sin observaciones"), 92));
		lineas.add("");
		lineas.add("");
		lineas.add("______________________________        ______________________________");
		lineas.add("Firma entrega                         Firma recepcion");
		lineas.add("");
		lineas.add("Aclaracion: ___________________        Aclaracion: ___________________");

		return pdf(lineas);
	}

	private byte[] pdf(List<String> lineas) {
		StringBuilder contenido = new StringBuilder();
		contenido.append("BT\n");
		contenido.append("/F1 16 Tf\n50 790 Td\n(").append(escape("Acta formal de inventario")).append(") Tj\n");
		contenido.append("/F1 10 Tf\n0 -26 Td\n");
		for (String linea : lineas) {
			contenido.append("(").append(escape(linea)).append(") Tj\n0 -15 Td\n");
		}
		contenido.append("ET\n");

		byte[] stream = contenido.toString().getBytes(StandardCharsets.ISO_8859_1);
		List<byte[]> objetos = List.of(
				"<< /Type /Catalog /Pages 2 0 R >>".getBytes(StandardCharsets.ISO_8859_1),
				"<< /Type /Pages /Kids [3 0 R] /Count 1 >>".getBytes(StandardCharsets.ISO_8859_1),
				"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
						.getBytes(StandardCharsets.ISO_8859_1),
				"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>".getBytes(StandardCharsets.ISO_8859_1),
				("<< /Length " + stream.length + " >>\nstream\n" + contenido + "endstream").getBytes(StandardCharsets.ISO_8859_1)
		);

		ByteArrayOutputStream salida = new ByteArrayOutputStream();
		write(salida, "%PDF-1.4\n");
		List<Integer> offsets = new ArrayList<>();
		for (int i = 0; i < objetos.size(); i++) {
			offsets.add(salida.size());
			write(salida, (i + 1) + " 0 obj\n");
			salida.writeBytes(objetos.get(i));
			write(salida, "\nendobj\n");
		}
		int xref = salida.size();
		write(salida, "xref\n0 " + (objetos.size() + 1) + "\n");
		write(salida, "0000000000 65535 f \n");
		for (Integer offset : offsets) {
			write(salida, String.format("%010d 00000 n \n", offset));
		}
		write(salida, "trailer\n<< /Size " + (objetos.size() + 1) + " /Root 1 0 R >>\nstartxref\n" + xref + "\n%%EOF\n");
		return salida.toByteArray();
	}

	private void write(ByteArrayOutputStream salida, String texto) {
		salida.writeBytes(texto.getBytes(StandardCharsets.ISO_8859_1));
	}

	private String texto(Object valor) {
		return texto(valor, "");
	}

	private String texto(Object valor, String fallback) {
		if (valor == null || valor.toString().trim().isEmpty()) {
			return fallback;
		}
		return valor.toString().trim();
	}

	private List<String> partir(String texto, int maximo) {
		List<String> lineas = new ArrayList<>();
		String restante = texto;
		while (restante.length() > maximo) {
			int corte = restante.lastIndexOf(' ', maximo);
			if (corte < 20) {
				corte = maximo;
			}
			lineas.add(restante.substring(0, corte).trim());
			restante = restante.substring(corte).trim();
		}
		lineas.add(restante);
		return lineas;
	}

	private String escape(String texto) {
		return texto
				.replace("\\", "\\\\")
				.replace("(", "\\(")
				.replace(")", "\\)")
				.replace("á", "a")
				.replace("é", "e")
				.replace("í", "i")
				.replace("ó", "o")
				.replace("ú", "u")
				.replace("Á", "A")
				.replace("É", "E")
				.replace("Í", "I")
				.replace("Ó", "O")
				.replace("Ú", "U")
				.replace("ñ", "n")
				.replace("Ñ", "N");
	}
}
