package ar.gov.justiciajujuy.sanpedro.inventario.equipos;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.EquipoDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.ReporteInventarioCommand;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class InventarioViejoImportService {

	private final EquipoService equipoService;
	private final ComponenteService componenteService;

	public InventarioViejoImportService(EquipoService equipoService, ComponenteService componenteService) {
		this.equipoService = equipoService;
		this.componenteService = componenteService;
	}

	@Transactional
	public ImportacionInventarioViejoResultado importarCsv(String contenidoCsv) {
		if (!StringUtils.hasText(contenidoCsv)) {
			return new ImportacionInventarioViejoResultado(0, 0, List.of("El contenido CSV esta vacio."));
		}

		List<String> lineas = contenidoCsv.lines()
				.filter(StringUtils::hasText)
				.toList();
		if (lineas.size() < 2) {
			return new ImportacionInventarioViejoResultado(0, 0, List.of("El CSV debe incluir encabezados y al menos una fila."));
		}

		List<String> encabezados = parsearLinea(lineas.get(0));
		int importados = 0;
		List<String> errores = new ArrayList<>();
		for (int i = 1; i < lineas.size(); i++) {
			Map<String, String> fila = mapearFila(encabezados, parsearLinea(lineas.get(i)));
			try {
				ReporteInventarioCommand command = toCommand(fila);
				EquipoDetalle equipo = equipoService.registrarInventario(command);
				componenteService.registrarDetectadosDesdeReporte(equipo.id(), command);
				importados++;
			} catch (RuntimeException ex) {
				errores.add("Fila " + (i + 1) + ": " + ex.getMessage());
			}
		}
		return new ImportacionInventarioViejoResultado(lineas.size() - 1, importados, errores);
	}

	private ReporteInventarioCommand toCommand(Map<String, String> fila) {
		String nombre = valor(fila, "nombre", "pcnombre", "equipo");
		if (!StringUtils.hasText(nombre)) {
			throw new IllegalArgumentException("falta nombre o PC_Nombre.");
		}
		return new ReporteInventarioCommand(
				nombre,
				valor(fila, "ultimousuario", "usuarioactual", "usuario"),
				valor(fila, "fuero", "area"),
				valor(fila, "ubicacion", "oficina"),
				valor(fila, "ip", "ipaddress"),
				valor(fila, "sistemaoperativo", "osname", "windows"),
				valor(fila, "procesador", "cpu"),
				ramMb(fila),
				valor(fila, "ramdetalles"),
				valor(fila, "ramseriales", "ramserials"),
				valor(fila, "discosmodelos", "diskmodels"),
				valor(fila, "discosseriales", "diskserials"),
				valor(fila, "motherboardmodelo", "motherboardmodel"),
				valor(fila, "motherboardserial", "motherboardsn"),
				valor(fila, "monitores", "monitors"),
				valor(fila, "teclado", "keyboardmodel"),
				valor(fila, "mouse", "mousemodel"),
				valor(fila, "impresora", "printermodel"),
				activo(fila));
	}

	private Integer ramMb(Map<String, String> fila) {
		String ramMb = valor(fila, "rammb");
		if (StringUtils.hasText(ramMb)) {
			return Integer.valueOf(ramMb.trim());
		}
		String ramGb = valor(fila, "ramgb", "ram");
		if (!StringUtils.hasText(ramGb)) {
			return null;
		}
		double gb = Double.parseDouble(ramGb.replace(',', '.').trim());
		return (int) Math.round(gb * 1024);
	}

	private boolean activo(Map<String, String> fila) {
		String valor = valor(fila, "activo");
		if (!StringUtils.hasText(valor)) {
			return true;
		}
		String normalizado = valor.trim().toLowerCase(Locale.ROOT);
		return !normalizado.equals("false") && !normalizado.equals("0") && !normalizado.equals("no");
	}

	private Map<String, String> mapearFila(List<String> encabezados, List<String> valores) {
		Map<String, String> fila = new LinkedHashMap<>();
		for (int i = 0; i < encabezados.size(); i++) {
			String clave = normalizarClave(encabezados.get(i));
			String valor = i < valores.size() ? valores.get(i).trim() : "";
			fila.put(clave, valor);
		}
		return fila;
	}

	private String valor(Map<String, String> fila, String... claves) {
		for (String clave : claves) {
			String valor = fila.get(clave);
			if (StringUtils.hasText(valor)) {
				return valor.trim();
			}
		}
		return null;
	}

	private String normalizarClave(String clave) {
		return clave.replace("\uFEFF", "")
				.toLowerCase(Locale.ROOT)
				.replaceAll("[^a-z0-9]", "");
	}

	private List<String> parsearLinea(String linea) {
		List<String> valores = new ArrayList<>();
		StringBuilder actual = new StringBuilder();
		boolean entreComillas = false;
		char delimitador = contar(linea, ';') > contar(linea, ',') ? ';' : ',';
		for (int i = 0; i < linea.length(); i++) {
			char caracter = linea.charAt(i);
			if (caracter == '"') {
				if (entreComillas && i + 1 < linea.length() && linea.charAt(i + 1) == '"') {
					actual.append('"');
					i++;
				} else {
					entreComillas = !entreComillas;
				}
			} else if (caracter == delimitador && !entreComillas) {
				valores.add(actual.toString());
				actual.setLength(0);
			} else {
				actual.append(caracter);
			}
		}
		valores.add(actual.toString());
		return valores;
	}

	private int contar(String texto, char buscado) {
		int cantidad = 0;
		for (int i = 0; i < texto.length(); i++) {
			if (texto.charAt(i) == buscado) {
				cantidad++;
			}
		}
		return cantidad;
	}

	public record ImportacionInventarioViejoResultado(
			int procesados,
			int importados,
			List<String> errores) {
	}
}
