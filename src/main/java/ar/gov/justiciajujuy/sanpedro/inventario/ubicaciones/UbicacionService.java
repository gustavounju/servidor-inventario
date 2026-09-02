package ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.auditoria.AuditoriaService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class UbicacionService {

	private final UbicacionRepository ubicacionRepository;
	private final AuditoriaService auditoriaService;

	public UbicacionService(UbicacionRepository ubicacionRepository, AuditoriaService auditoriaService) {
		this.ubicacionRepository = ubicacionRepository;
		this.auditoriaService = auditoriaService;
	}

	@Transactional(readOnly = true)
	public List<UbicacionDetalle> buscar(String query, TipoUbicacion tipo, EstadoUbicacion estado) {
		return ubicacionRepository.buscar(textoOpcional(query), tipo, estado).stream()
				.map(this::toDetalle)
				.toList();
	}

	@Transactional(readOnly = true)
	public List<UbicacionDetalle> activas() {
		return buscar(null, null, EstadoUbicacion.ACTIVA);
	}

	@Transactional
	public UbicacionDetalle crear(GuardarUbicacionCommand command) {
		String codigo = textoRequerido(command.codigo(), "codigo");
		exigirCodigoDisponible(codigo, null);
		Ubicacion ubicacion = new Ubicacion(
				codigo,
				textoRequerido(command.nombre(), "nombre"),
				command.tipo() == null ? TipoUbicacion.OFICINA : command.tipo());
		aplicar(ubicacion, command);
		Ubicacion guardada = ubicacionRepository.save(ubicacion);
		auditoriaService.registrar("UBICACIONES", "CREAR", "Ubicacion", guardada.getId(),
				"Ubicacion " + guardada.getCodigo() + " creada.");
		return toDetalle(guardada);
	}

	@Transactional
	public UbicacionDetalle actualizar(Long id, GuardarUbicacionCommand command) {
		Ubicacion ubicacion = ubicacionRepository.findById(id).orElseThrow(() -> new UbicacionNoEncontradaException(id));
		exigirCodigoDisponible(textoRequerido(command.codigo(), "codigo"), id);
		aplicar(ubicacion, command);
		Ubicacion guardada = ubicacionRepository.save(ubicacion);
		auditoriaService.registrar("UBICACIONES", "ACTUALIZAR", "Ubicacion", guardada.getId(),
				"Ubicacion " + guardada.getCodigo() + " actualizada.");
		return toDetalle(guardada);
	}

	public long contar() {
		return ubicacionRepository.count();
	}

	private void aplicar(Ubicacion ubicacion, GuardarUbicacionCommand command) {
		ubicacion.actualizar(
				textoRequerido(command.codigo(), "codigo"),
				textoRequerido(command.nombre(), "nombre"),
				command.tipo() == null ? TipoUbicacion.OFICINA : command.tipo(),
				textoOpcional(command.fuero()),
				textoOpcional(command.responsable()),
				textoOpcional(command.edificio()),
				textoOpcional(command.piso()),
				command.estado() == null ? EstadoUbicacion.ACTIVA : command.estado(),
				textoOpcional(command.observaciones()),
				command.activo());
	}

	private UbicacionDetalle toDetalle(Ubicacion ubicacion) {
		return new UbicacionDetalle(
				ubicacion.getId(),
				ubicacion.getCodigo(),
				ubicacion.getNombre(),
				ubicacion.getTipo(),
				ubicacion.getFuero(),
				ubicacion.getResponsable(),
				ubicacion.getEdificio(),
				ubicacion.getPiso(),
				ubicacion.getEstado(),
				ubicacion.getObservaciones(),
				ubicacion.isActivo());
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

	private void exigirCodigoDisponible(String codigo, Long idActual) {
		ubicacionRepository.findByCodigoIgnoreCase(codigo)
				.filter(ubicacion -> idActual == null || !ubicacion.getId().equals(idActual))
				.ifPresent(ubicacion -> {
					throw new UbicacionDuplicadaException(codigo);
				});
	}

	public record GuardarUbicacionCommand(String codigo, String nombre, TipoUbicacion tipo, String fuero,
			String responsable, String edificio, String piso, EstadoUbicacion estado, String observaciones,
			boolean activo) {
	}

	public record UbicacionDetalle(Long id, String codigo, String nombre, TipoUbicacion tipo, String fuero,
			String responsable, String edificio, String piso, EstadoUbicacion estado, String observaciones,
			boolean activo) {
	}

	public static class UbicacionNoEncontradaException extends RuntimeException {
		public UbicacionNoEncontradaException(Long id) {
			super("Ubicacion no encontrada: " + id);
		}
	}

	public static class UbicacionDuplicadaException extends RuntimeException {
		public UbicacionDuplicadaException(String codigo) {
			super("Ya existe una ubicacion con codigo: " + codigo);
		}
	}
}
