package ar.gov.justiciajujuy.sanpedro.inventario.componentes;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.auditoria.AuditoriaService;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.Equipo;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.EquipoNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.ReporteInventarioCommand;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class ComponenteService {

	private final ComponenteRepository componenteRepository;
	private final EquipoRepository equipoRepository;
	private final AuditoriaService auditoriaService;

	public ComponenteService(ComponenteRepository componenteRepository, EquipoRepository equipoRepository,
			AuditoriaService auditoriaService) {
		this.componenteRepository = componenteRepository;
		this.equipoRepository = equipoRepository;
		this.auditoriaService = auditoriaService;
	}

	@Transactional(readOnly = true)
	public List<ComponenteDetalle> listarPorEquipo(Long equipoId) {
		return componenteRepository.findByEquipoIdOrderByTipoAscDescripcionAsc(equipoId).stream()
				.map(this::toDetalle)
				.toList();
	}

	@Transactional
	public ComponenteDetalle crear(Long equipoId, GuardarComponenteCommand command) {
		Equipo equipo = equipoRepository.findById(equipoId)
				.orElseThrow(() -> new EquipoNoEncontradoException(equipoId));
		Componente componente = new Componente(
				equipo,
				command.tipo(),
				command.origen(),
				command.estadoComparacion(),
				textoRequerido(command.descripcion(), "descripcion"));
		aplicarCampos(componente, command);
		Componente guardado = componenteRepository.save(componente);
		auditoriaService.registrar("COMPONENTES", "CREAR", "Componente", guardado.getId(),
				"Componente " + guardado.getTipo() + " creado para equipo " + equipo.getNombre() + " con origen " + guardado.getOrigen() + ".");
		return toDetalle(guardado);
	}

	@Transactional
	public ComponenteDetalle actualizar(Long id, GuardarComponenteCommand command) {
		Componente componente = componenteRepository.findById(id)
				.orElseThrow(() -> new ComponenteNoEncontradoException(id));
		aplicarCampos(componente, command);
		Componente guardado = componenteRepository.save(componente);
		auditoriaService.registrar("COMPONENTES", "ACTUALIZAR", "Componente", guardado.getId(),
				"Componente " + guardado.getTipo() + " actualizado con origen " + guardado.getOrigen() + " y estado " + guardado.getEstadoComparacion() + ".");
		return toDetalle(guardado);
	}

	@Transactional(readOnly = true)
	public Componente obtenerEntidad(Long id) {
		return componenteRepository.findById(id)
				.orElseThrow(() -> new ComponenteNoEncontradoException(id));
	}

	@Transactional
	public List<ComponenteDetalle> consolidarRelevamientoInicial(Long equipoId) {
		Equipo equipo = equipoRepository.findById(equipoId)
				.orElseThrow(() -> new EquipoNoEncontradoException(equipoId));
		List<Componente> detectados = componenteRepository.findByEquipoIdAndOrigenOrderByTipoAscDescripcionAsc(equipoId, OrigenComponente.SCRIPT);
		componenteRepository.deleteByEquipoIdAndOrigen(equipoId, OrigenComponente.RELEVAMIENTO_INICIAL);
		for (Componente detectado : detectados) {
			if (!detectado.isActivo()) {
				continue;
			}
			Componente relevado = new Componente(
					equipo,
					detectado.getTipo(),
					OrigenComponente.RELEVAMIENTO_INICIAL,
					EstadoComparacion.ESPERADO,
					detectado.getDescripcion());
			relevado.actualizar(
					detectado.getTipo(),
					OrigenComponente.RELEVAMIENTO_INICIAL,
					EstadoComparacion.ESPERADO,
					detectado.getDescripcion(),
					detectado.getMarca(),
					detectado.getModelo(),
					detectado.getSerial(),
					detectado.getCapacidad(),
					detectado.getUbicacion(),
					observacionConsolidada(detectado.getObservaciones()),
					true);
			componenteRepository.save(relevado);
		}
		auditoriaService.registrar("COMPONENTES", "CONSOLIDAR_RELEVAMIENTO_INICIAL", "Equipo", equipoId,
				"Se consolido la lectura SCRIPT como RELEVAMIENTO_INICIAL para " + equipo.getNombre() + ".");
		return listarPorEquipo(equipoId);
	}

	@Transactional
	public List<ComponenteDetalle> registrarDetectadosDesdeReporte(Long equipoId, ReporteInventarioCommand command) {
		Equipo equipo = equipoRepository.findById(equipoId)
				.orElseThrow(() -> new EquipoNoEncontradoException(equipoId));
		componenteRepository.deleteByEquipoIdAndOrigen(equipoId, OrigenComponente.SCRIPT);
		registrarSiHayDato(equipo, TipoComponente.CPU, "Procesador detectado", null, command.procesador(), null, null, "CPU", command.procesador());
		registrarRamDetectada(equipo, command.ramDetalles(), command.ramSeriales());
		registrarDiscosDetectados(equipo, command.discosModelos(), command.discosSeriales());
		registrarSiHayDato(equipo, TipoComponente.MOTHERBOARD, "Motherboard detectada", null, command.motherboardModelo(), command.motherboardSerial(), null, "Placa madre", command.motherboardModelo());
		registrarListaSimple(equipo, TipoComponente.MONITOR, "Monitor detectado", command.monitores(), "Puesto de trabajo");
		registrarSiHayDato(equipo, TipoComponente.TECLADO, "Teclado detectado", null, command.teclado(), null, null, "Puesto de trabajo", command.teclado());
		registrarSiHayDato(equipo, TipoComponente.MOUSE, "Mouse detectado", null, command.mouse(), null, null, "Puesto de trabajo", command.mouse());
		registrarSiHayDato(equipo, TipoComponente.IMPRESORA, "Impresora detectada", null, command.impresora(), null, null, "Puesto de trabajo", command.impresora());
		auditoriaService.registrar("COMPONENTES", "REGISTRAR_SCRIPT", "Equipo", equipoId,
				"Se registraron componentes detectados por script para " + equipo.getNombre() + ".");
		return listarPorEquipo(equipoId);
	}

	private void aplicarCampos(Componente componente, GuardarComponenteCommand command) {
		componente.actualizar(
				command.tipo(),
				command.origen(),
				command.estadoComparacion(),
				textoRequerido(command.descripcion(), "descripcion"),
				textoOpcional(command.marca()),
				textoOpcional(command.modelo()),
				textoOpcional(command.serial()),
				textoOpcional(command.capacidad()),
				textoOpcional(command.ubicacion()),
				textoOpcional(command.observaciones()),
				command.activo());
	}

	private void registrarRamDetectada(Equipo equipo, String detalles, String seriales) {
		List<String> partes = separar(detalles);
		List<String> series = separar(seriales);
		int total = Math.max(partes.size(), series.size());
		for (int i = 0; i < total; i++) {
			String detalle = valorEn(partes, i);
			String serial = valorEn(series, i);
			registrarSiHayDato(equipo, TipoComponente.RAM, "Modulo RAM detectado", null, detalle, serial, detalle, "Slot RAM", detalle != null ? detalle : serial);
		}
	}

	private void registrarDiscosDetectados(Equipo equipo, String modelos, String seriales) {
		List<String> partes = separar(modelos);
		List<String> series = separar(seriales);
		int total = Math.max(partes.size(), series.size());
		for (int i = 0; i < total; i++) {
			String modelo = valorEn(partes, i);
			String serial = valorEn(series, i);
			registrarSiHayDato(equipo, TipoComponente.DISCO, "Disco detectado", null, modelo, serial, null, "Bahia/puerto de disco", modelo != null ? modelo : serial);
		}
	}

	private void registrarListaSimple(Equipo equipo, TipoComponente tipo, String descripcion, String valores, String ubicacion) {
		for (String valor : separar(valores)) {
			registrarSiHayDato(equipo, tipo, descripcion, null, valor, extraerSerial(valor), null, ubicacion, valor);
		}
	}

	private void registrarSiHayDato(Equipo equipo, TipoComponente tipo, String descripcion, String marca, String modelo,
			String serial, String capacidad, String ubicacion, String datoMinimo) {
		if (!StringUtils.hasText(datoMinimo)) {
			return;
		}
		Componente componente = new Componente(equipo, tipo, OrigenComponente.SCRIPT, EstadoComparacion.DETECTADO, descripcion);
		componente.actualizar(tipo, OrigenComponente.SCRIPT, EstadoComparacion.DETECTADO, descripcion,
				textoOpcional(marca), textoOpcional(modelo), textoOpcional(serial), textoOpcional(capacidad),
				textoOpcional(ubicacion), "Detectado por script de inventario.", true);
		componenteRepository.save(componente);
	}

	private List<String> separar(String valor) {
		if (!StringUtils.hasText(valor)) {
			return List.of();
		}
		return java.util.Arrays.stream(valor.split("\\|"))
				.map(String::trim)
				.filter(StringUtils::hasText)
				.toList();
	}

	private String valorEn(List<String> valores, int index) {
		return index < valores.size() ? valores.get(index) : null;
	}

	private String extraerSerial(String valor) {
		if (!StringUtils.hasText(valor)) {
			return null;
		}
		String[] partes = valor.trim().split("\\s+");
		return partes.length > 0 ? partes[partes.length - 1] : null;
	}

	private String observacionConsolidada(String observacionesDetectadas) {
		String base = "Consolidado como relevamiento inicial desde la ultima lectura del script.";
		if (!StringUtils.hasText(observacionesDetectadas)) {
			return base;
		}
		return base + " Observacion original: " + observacionesDetectadas.trim();
	}

	private ComponenteDetalle toDetalle(Componente componente) {
		return new ComponenteDetalle(
				componente.getId(),
				componente.getEquipo().getId(),
				componente.getTipo(),
				componente.getOrigen(),
				componente.getEstadoComparacion(),
				componente.getDescripcion(),
				componente.getMarca(),
				componente.getModelo(),
				componente.getSerial(),
				componente.getCapacidad(),
				componente.getUbicacion(),
				componente.getObservaciones(),
				componente.isActivo());
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

	public record GuardarComponenteCommand(
			TipoComponente tipo,
			OrigenComponente origen,
			EstadoComparacion estadoComparacion,
			String descripcion,
			String marca,
			String modelo,
			String serial,
			String capacidad,
			String ubicacion,
			String observaciones,
			boolean activo) {
	}

	public record ComponenteDetalle(
			Long id,
			Long equipoId,
			TipoComponente tipo,
			OrigenComponente origen,
			EstadoComparacion estadoComparacion,
			String descripcion,
			String marca,
			String modelo,
			String serial,
			String capacidad,
			String ubicacion,
			String observaciones,
			boolean activo) {
	}

	public static class ComponenteNoEncontradoException extends RuntimeException {

		public ComponenteNoEncontradoException(Long id) {
			super("Componente no encontrado: " + id);
		}
	}
}
