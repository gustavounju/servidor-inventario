package ar.gov.justiciajujuy.sanpedro.inventario.equipos;

import java.time.Clock;
import java.time.LocalDateTime;
import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class EquipoService {

	private final EquipoRepository equipoRepository;
	private final FueroService fueroService;
	private final Clock clock;

	@Autowired
	public EquipoService(EquipoRepository equipoRepository, FueroService fueroService) {
		this(equipoRepository, fueroService, Clock.systemDefaultZone());
	}

	EquipoService(EquipoRepository equipoRepository, FueroService fueroService, Clock clock) {
		this.equipoRepository = equipoRepository;
		this.fueroService = fueroService;
		this.clock = clock;
	}

	@Transactional(readOnly = true)
	public EquipoPagina listar(String query, int page, int pageSize) {
		int pagina = Math.max(0, page);
		int tamano = Math.max(1, Math.min(pageSize, 100));
		String filtro = StringUtils.hasText(query) ? query.trim() : null;
		Page<Equipo> resultado = equipoRepository.buscar(
				filtro,
				PageRequest.of(pagina, tamano, Sort.by("nombre").ascending()));
		return new EquipoPagina(
				resultado.getContent().stream().map(this::toResumen).toList(),
				new Paginacion(resultado.getNumber(), resultado.getSize(), resultado.getTotalElements(), resultado.getTotalPages()));
	}

	@Transactional(readOnly = true)
	public EquipoDetalle obtener(Long id) {
		return equipoRepository.findById(id)
				.map(this::toDetalle)
				.orElseThrow(() -> new EquipoNoEncontradoException(id));
	}

	private static final java.util.Map<String, String> DEFAULT_FUERO_MAPPING = java.util.Map.ofEntries(
			java.util.Map.entry("TTSIVVOC", "Tribunal de Trabajo Sala IV"),
			java.util.Map.entry("OGL", "Oficina de Gestion Laboral"),
			java.util.Map.entry("SISTEMAS", "Dpto. Informatica San Pedro"),
			java.util.Map.entry("VGS", "Violencia de Género 5"),
			java.util.Map.entry("VG5", "Violencia de Género 5"),
			java.util.Map.entry("SIVL", "Sala IV Laboral"),
			java.util.Map.entry("TJO1", "Tribunal de Juicio"),
			java.util.Map.entry("TJ01", "Tribunal de Juicio"),
			java.util.Map.entry("TJ", "Tribunal de Juicio"),
			java.util.Map.entry("CGESE", "Cámara Gesell"),
			java.util.Map.entry("JCC8SEC16", "Juzgado civil y Comercial N°8 Secretaria 16"),
			java.util.Map.entry("JCC9SEC18", "Juzgado civil y Comercial N°9 Secretaria 18"),
			java.util.Map.entry("JCC", "Juzgado Civil y Comercial"),
			java.util.Map.entry("CCYCSIV", "Cámara Civil y Comercial Sala IV"),
			java.util.Map.entry("CCYC", "Cámara Civil y Comercial"),
			java.util.Map.entry("PRENSA", "Prensa Poder Judicial de San Pedro de Jujuy"),
			java.util.Map.entry("SUPINT", "Superintendencia"),
			java.util.Map.entry("EQINT", "Equipo Interdisciplinario"),
			java.util.Map.entry("JUZMEN2", "Juzgado de Menores 2"),
			java.util.Map.entry("JUZMEN", "Juzgado de Menores"),
			java.util.Map.entry("JMEN", "Juzgado de Menores"),
			java.util.Map.entry("OGJ", "Oficina de Gestion Judicial"),
			java.util.Map.entry("VIOGEN", "Violencia de Género 5"),
			java.util.Map.entry("TFSIIIV", "Tribunal de Familia - Sala III"),
			java.util.Map.entry("TRIBJU", "Tribunal de Juicio"),
			java.util.Map.entry("FAM", "Juzgado de Familia"),
			java.util.Map.entry("JF", "Juzgado de Familia"),
			java.util.Map.entry("JFAM", "Juzgado de Familia"),
			java.util.Map.entry("CORP", "Juzgado de Control - Corp."),
			java.util.Map.entry("JCON", "Juzgado de Control"),
			java.util.Map.entry("OMN", "Mandamientos y Notificaciones"),
			java.util.Map.entry("OM", "Oficina de Mandamientos"),
			java.util.Map.entry("NOT", "Oficina de Notificaciones"),
			java.util.Map.entry("BIB", "Biblioteca"),
			java.util.Map.entry("ARQ", "Archivo"),
			java.util.Map.entry("INT", "Intendencia"),
			java.util.Map.entry("MAY", "Mayordomia"),
			java.util.Map.entry("MED", "Reconocimiento Medico"),
			java.util.Map.entry("PSI", "Psicologia"),
			java.util.Map.entry("TS", "Trabajo Social"),
			java.util.Map.entry("MESA", "Mesa de Entradas"),
			java.util.Map.entry("ME", "Mesa de Entradas"),
			java.util.Map.entry("VOC", "Vocalia"),
			java.util.Map.entry("DP", "Defensoria Publica"),
			java.util.Map.entry("DEF", "Defensoria"),
			java.util.Map.entry("MPA", "Ministerio Publico Acusacion"),
			java.util.Map.entry("SIGJ", "Sistemas SIGJ")
	);

	private String detectarFuero(String pcName) {
		if (pcName == null) {
			return "Desconocido";
		}
		String pcUpper = pcName.toUpperCase();
		String bestMatch = "Desconocido";
		int longestPrefixLen = -1;

		for (java.util.Map.Entry<String, String> entry : DEFAULT_FUERO_MAPPING.entrySet()) {
			String prefix = entry.getKey().toUpperCase();
			if (pcUpper.startsWith(prefix)) {
				if (prefix.length() > longestPrefixLen) {
					longestPrefixLen = prefix.length();
					bestMatch = entry.getValue();
				}
			}
		}
		return bestMatch;
	}

	@Transactional
	public EquipoDetalle registrarInventario(ReporteInventarioCommand command) {
		String nombre = normalizarNombre(command.nombre());
		
		String fuero = null;
		Equipo equipoExistente = equipoRepository.findByNombreIgnoreCase(nombre).orElse(null);
		if (command.fuero() != null && StringUtils.hasText(command.fuero())) {
			fuero = command.fuero().trim();
		} else if (equipoExistente != null && StringUtils.hasText(equipoExistente.getFuero()) && !"Desconocido".equalsIgnoreCase(equipoExistente.getFuero())) {
			fuero = equipoExistente.getFuero();
		} else {
			fuero = fueroService.resolverFuero(command.fuero(), nombre);
		}

		Equipo equipo = equipoExistente != null ? equipoExistente : new Equipo(nombre, fuero);
		equipo.actualizarDesdeReporte(
				textoOpcional(command.ultimoUsuario()),
				fuero,
				textoOpcional(command.ubicacion()),
				textoOpcional(command.ip()),
				textoOpcional(command.sistemaOperativo()),
				textoOpcional(command.procesador()),
				command.ramMb(),
				textoOpcional(command.ramDetalles()),
				textoOpcional(command.ramSeriales()),
				textoOpcional(command.discosModelos()),
				textoOpcional(command.discosSeriales()),
				textoOpcional(command.motherboardModelo()),
				textoOpcional(command.motherboardSerial()),
				textoOpcional(command.monitores()),
				textoOpcional(command.teclado()),
				textoOpcional(command.mouse()),
				textoOpcional(command.impresora()),
				command.activo(),
				LocalDateTime.now(clock));
		return toDetalle(equipoRepository.save(equipo));
	}

	@Transactional
	public EquipoDetalle actualizarManualmente(Long id, ActualizarEquipoCommand command) {
		Equipo equipo = equipoRepository.findById(id)
				.orElseThrow(() -> new EquipoNoEncontradoException(id));
		String nombre = normalizarNombre(command.nombre());
		equipoRepository.findByNombreIgnoreCase(nombre)
				.filter(existente -> !existente.getId().equals(id))
				.ifPresent(existente -> {
					throw new EquipoDuplicadoException(nombre);
				});
		equipo.actualizarManualmente(
				nombre,
				textoOpcional(command.ultimoUsuario()),
				textoRequerido(command.fuero(), "fuero"),
				textoOpcional(command.ubicacion()),
				textoOpcional(command.ip()),
				textoOpcional(command.sistemaOperativo()),
				textoOpcional(command.procesador()),
				command.ramMb(),
				textoOpcional(command.ramDetalles()),
				textoOpcional(command.ramSeriales()),
				textoOpcional(command.discosModelos()),
				textoOpcional(command.discosSeriales()),
				textoOpcional(command.motherboardModelo()),
				textoOpcional(command.motherboardSerial()),
				textoOpcional(command.monitores()),
				textoOpcional(command.teclado()),
				textoOpcional(command.mouse()),
				textoOpcional(command.impresora()),
				command.activo());
		return toDetalle(equipoRepository.save(equipo));
	}

	/**
	 * Crea de forma ágil una estación en el Taller de Informática para iniciar su ensamblado.
	 * Si no se indica un código manual, genera correlativamente un nombre secuencial libre
	 * con el formato 'ARMADO-001', 'ARMADO-002', etc., evitando colisiones.
	 *
	 * @param codigoSugerido Código opcional ingresado por el técnico o nulo/vacío para autogenerar
	 * @return Detalle del equipo creado y persistido con ubicación y fuero de taller
	 * @throws EquipoDuplicadoException Si el código sugerido ya existe en la base de datos
	 */
	@Transactional
	public EquipoDetalle crearEquipoEnTaller(String codigoSugerido) {
		String nombre;
		if (StringUtils.hasText(codigoSugerido)) {
			nombre = normalizarNombre(codigoSugerido);
			if (equipoRepository.findByNombreIgnoreCase(nombre).isPresent()) {
				throw new EquipoDuplicadoException(nombre);
			}
		} else {
			int seq = 1;
			do {
				nombre = String.format("ARMADO-%03d", seq++);
			} while (equipoRepository.findByNombreIgnoreCase(nombre).isPresent());
		}

		Equipo equipo = Equipo.crearParaTaller(nombre);
		return toDetalle(equipoRepository.save(equipo));
	}

	private EquipoResumen toResumen(Equipo equipo) {
		return new EquipoResumen(
				equipo.getId(),
				equipo.getNombre(),
				equipo.getUltimoUsuario(),
				equipo.getFuero(),
				equipo.getUbicacion(),
				equipo.getIp(),
				equipo.getSistemaOperativo(),
				equipo.getMonitoreo(),
				equipo.isActivo(),
				equipo.getUltimoReporteEn());
	}

	private EquipoDetalle toDetalle(Equipo equipo) {
		return new EquipoDetalle(
				equipo.getId(),
				equipo.getNombre(),
				equipo.getUltimoUsuario(),
				equipo.getFuero(),
				equipo.getUbicacion(),
				equipo.getIp(),
				equipo.getSistemaOperativo(),
				equipo.getProcesador(),
				equipo.getRamMb(),
				equipo.getRamDetalles(),
				equipo.getRamSeriales(),
				equipo.getDiscosModelos(),
				equipo.getDiscosSeriales(),
				equipo.getMotherboardModelo(),
				equipo.getMotherboardSerial(),
				equipo.getMonitores(),
				equipo.getTeclado(),
				equipo.getMouse(),
				equipo.getImpresora(),
				equipo.getMonitoreo(),
				equipo.isActivo(),
				equipo.getUltimoReporteEn());
	}

	private String normalizarNombre(String nombre) {
		return nombre.trim().toUpperCase();
	}

	private String textoOpcional(String valor) {
		return StringUtils.hasText(valor) ? valor.trim() : null;
	}

	private String textoRequerido(String valor, String campo) {
		if (!StringUtils.hasText(valor)) {
			throw new IllegalArgumentException("El campo " + campo + " es obligatorio.");
		}
		return valor.trim();
	}

	public record ReporteInventarioCommand(
			String nombre,
			String ultimoUsuario,
			String fuero,
			String ubicacion,
			String ip,
			String sistemaOperativo,
			String procesador,
			Integer ramMb,
			String ramDetalles,
			String ramSeriales,
			String discosModelos,
			String discosSeriales,
			String motherboardModelo,
			String motherboardSerial,
			String monitores,
			String teclado,
			String mouse,
			String impresora,
			boolean activo) {
	}

	public record ActualizarEquipoCommand(
			String nombre,
			String ultimoUsuario,
			String fuero,
			String ubicacion,
			String ip,
			String sistemaOperativo,
			String procesador,
			Integer ramMb,
			String ramDetalles,
			String ramSeriales,
			String discosModelos,
			String discosSeriales,
			String motherboardModelo,
			String motherboardSerial,
			String monitores,
			String teclado,
			String mouse,
			String impresora,
			boolean activo) {
	}

	public record EquipoPagina(List<EquipoResumen> equipos, Paginacion paginacion) {
	}

	public record Paginacion(int page, int pageSize, long totalItems, int totalPages) {
	}

	public record EquipoResumen(
			Long id,
			String nombre,
			String ultimoUsuario,
			String fuero,
			String ubicacion,
			String ip,
			String sistemaOperativo,
			String monitoreo,
			boolean activo,
			LocalDateTime ultimoReporteEn) {
	}

	public record EquipoDetalle(
			Long id,
			String nombre,
			String ultimoUsuario,
			String fuero,
			String ubicacion,
			String ip,
			String sistemaOperativo,
			String procesador,
			Integer ramMb,
			String ramDetalles,
			String ramSeriales,
			String discosModelos,
			String discosSeriales,
			String motherboardModelo,
			String motherboardSerial,
			String monitores,
			String teclado,
			String mouse,
			String impresora,
			String monitoreo,
			boolean activo,
			LocalDateTime ultimoReporteEn) {
	}

	public static class EquipoNoEncontradoException extends RuntimeException {

		public EquipoNoEncontradoException(Long id) {
			super("Equipo no encontrado: " + id);
		}
	}

	public static class EquipoDuplicadoException extends RuntimeException {

		public EquipoDuplicadoException(String nombre) {
			super("Ya existe un equipo con nombre: " + nombre);
		}
	}
}
