package ar.gov.justiciajujuy.sanpedro.inventario.actas;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

import org.springframework.stereotype.Service;

@Service
public class ActaPdfService {

	private static final DateTimeFormatter FECHA = DateTimeFormatter.ofPattern("dd/MM/yyyy");

	public byte[] generar(ActaService.ActaDetalle acta) {
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
