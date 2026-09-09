package ar.gov.justiciajujuy.sanpedro.inventario.tareas;

import java.time.LocalDateTime;
import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.auditoria.AuditoriaService;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.Equipo;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class TareaTecnicaService {

	public static final String EQUIPO_GENERICO_NOMBRE = "PC-GENERICA";

	private final TareaTecnicaRepository tareaTecnicaRepository;
	private final TareaTecnicaComentarioRepository comentarioRepository;
	private final EquipoRepository equipoRepository;
	private final AuditoriaService auditoriaService;

	public TareaTecnicaService(
			TareaTecnicaRepository tareaTecnicaRepository,
			TareaTecnicaComentarioRepository comentarioRepository,
			EquipoRepository equipoRepository,
			AuditoriaService auditoriaService) {
		this.tareaTecnicaRepository = tareaTecnicaRepository;
		this.comentarioRepository = comentarioRepository;
		this.equipoRepository = equipoRepository;
		this.auditoriaService = auditoriaService;
	}

	@Transactional(readOnly = true)
	public List<TareaTecnicaDetalle> buscar(EstadoTareaTecnica estado, Long equipoId, String responsable) {
		return tareaTecnicaRepository.buscar(estado, equipoId, textoOpcional(responsable)).stream()
				.map(this::toDetalle)
				.toList();
	}

	@Transactional(readOnly = true)
	public TareaTecnicaDetalle obtener(Long id) {
		return tareaTecnicaRepository.findById(id)
				.map(this::toDetalle)
				.orElseThrow(() -> new TareaTecnicaNoEncontradaException(id));
	}

	public long contar() {
		return tareaTecnicaRepository.count();
	}

	@Transactional(readOnly = true)
	public List<TareaComentarioDetalle> comentarios(Long tareaId) {
		validarExistencia(tareaId);
		return comentarioRepository.findByTareaIdOrderByCreadoEnDescIdDesc(tareaId).stream()
				.map(this::toComentarioDetalle)
				.toList();
	}

	@Transactional
	public TareaTecnicaDetalle crear(GuardarTareaTecnicaCommand command) {
		TareaTecnica tarea = new TareaTecnica(textoRequerido(command.titulo(), "titulo"));
		tarea.actualizarDatos(
				buscarEquipoParaTarea(command.equipoId()),
				textoRequerido(command.titulo(), "titulo"),
				textoOpcional(command.descripcion()),
				textoRequerido(command.solicitanteUsername(), "solicitante"),
				textoRequerido(command.solicitanteNombre(), "solicitanteNombre"),
				textoRequerido(command.solicitanteFuero(), "solicitanteFuero"),
				command.prioridad() == null ? PrioridadTareaTecnica.MEDIA : command.prioridad(),
				textoOpcional(command.responsable()));
		tarea.marcarCreadoPor(textoOpcional(command.creadoPor()));
		TareaTecnica guardada = tareaTecnicaRepository.save(tarea);
		auditoriaService.registrar("TAREAS", "CREAR", "TareaTecnica", guardada.getId(),
				"Tarea tecnica creada: " + guardada.getTitulo() + ".");
		return toDetalle(guardada);
	}

	@Transactional
	public TareaTecnicaDetalle actualizar(Long id, GuardarTareaTecnicaCommand command) {
		TareaTecnica tarea = tareaTecnicaRepository.findById(id)
				.orElseThrow(() -> new TareaTecnicaNoEncontradaException(id));
		tarea.actualizarDatos(
				buscarEquipoParaTarea(command.equipoId()),
				textoRequerido(command.titulo(), "titulo"),
				textoOpcional(command.descripcion()),
				textoRequerido(command.solicitanteUsername(), "solicitante"),
				textoRequerido(command.solicitanteNombre(), "solicitanteNombre"),
				textoRequerido(command.solicitanteFuero(), "solicitanteFuero"),
				command.prioridad() == null ? PrioridadTareaTecnica.MEDIA : command.prioridad(),
				textoOpcional(command.responsable()));
		auditoriaService.registrar("TAREAS", "ACTUALIZAR", "TareaTecnica", tarea.getId(),
				"Tarea tecnica " + tarea.getId() + " actualizada.");
		return toDetalle(tarea);
	}

	@Transactional
	public TareaTecnicaDetalle tomar(Long id, String responsable) {
		TareaTecnica tarea = tareaTecnicaRepository.findById(id)
				.orElseThrow(() -> new TareaTecnicaNoEncontradaException(id));
		String responsableNormalizado = textoRequerido(responsable, "responsable");
		if (StringUtils.hasText(tarea.getResponsable()) && !tarea.getResponsable().equalsIgnoreCase(responsableNormalizado)) {
			throw new TareaTecnicaYaAsignadaException(id, tarea.getResponsable());
		}
		tarea.tomar(responsableNormalizado);
		auditoriaService.registrar("TAREAS", "TOMAR", "TareaTecnica", tarea.getId(),
				"Tarea tecnica " + tarea.getId() + " tomada por " + responsableNormalizado + ".");
		return toDetalle(tarea);
	}

	@Transactional
	public TareaTecnicaDetalle reasignarEquipo(Long id, Long equipoDestinoId, String usuario) {
		TareaTecnica tarea = tareaTecnicaRepository.findById(id)
				.orElseThrow(() -> new TareaTecnicaNoEncontradaException(id));
		Equipo equipoDestino = buscarEquipoOpcional(equipoDestinoId);
		if (EQUIPO_GENERICO_NOMBRE.equalsIgnoreCase(equipoDestino.getNombre())) {
			throw new IllegalArgumentException("La tarea ya se encuentra en la PC generica auxiliar.");
		}
		tarea.reasignarEquipo(equipoDestino);
		auditoriaService.registrar("TAREAS", "REASIGNAR_EQUIPO", "TareaTecnica", tarea.getId(),
				"Tarea tecnica " + tarea.getId() + " reasignada al equipo " + equipoDestino.getNombre()
						+ " por " + textoOpcional(usuario) + ".");
		return toDetalle(tarea);
	}

	@Transactional
	public TareaTecnicaDetalle cambiarEstado(Long id, CambiarEstadoTareaCommand command) {
		TareaTecnica tarea = tareaTecnicaRepository.findById(id)
				.orElseThrow(() -> new TareaTecnicaNoEncontradaException(id));
		EstadoTareaTecnica estado = command.estado() == null ? EstadoTareaTecnica.PENDIENTE : command.estado();
		tarea.cambiarEstado(estado, textoOpcional(command.observacionesCierre()));
		auditoriaService.registrar("TAREAS", "CAMBIAR_ESTADO", "TareaTecnica", tarea.getId(),
				"Tarea tecnica " + tarea.getId() + " cambio a " + estado + ".");
		return toDetalle(tarea);
	}

	@Transactional
	public TareaComentarioDetalle comentar(Long id, AgregarComentarioTareaCommand command) {
		TareaTecnica tarea = tareaTecnicaRepository.findById(id)
				.orElseThrow(() -> new TareaTecnicaNoEncontradaException(id));
		TareaTecnicaComentario comentario = comentarioRepository.save(new TareaTecnicaComentario(
				tarea,
				textoRequerido(command.autor(), "autor"),
				textoRequerido(command.comentario(), "comentario")));
		auditoriaService.registrar("TAREAS", "COMENTAR", "TareaTecnica", tarea.getId(),
				"Comentario agregado a tarea tecnica " + tarea.getId() + ".");
		return toComentarioDetalle(comentario);
	}

	@Transactional
	public void eliminar(Long id) {
		TareaTecnica tarea = tareaTecnicaRepository.findById(id)
				.orElseThrow(() -> new TareaTecnicaNoEncontradaException(id));
		String titulo = tarea.getTitulo();
		comentarioRepository.deleteByTareaId(id);
		tareaTecnicaRepository.delete(tarea);
		auditoriaService.registrar("TAREAS", "ELIMINAR", "TareaTecnica", id,
				"Tarea técnica " + id + " (" + titulo + ") eliminada.");
	}

	private Equipo buscarEquipoOpcional(Long equipoId) {
		if (equipoId == null) {
			return null;
		}
		return equipoRepository.findById(equipoId)
				.orElseThrow(() -> new EquipoNoEncontradoException(equipoId));
	}

	private Equipo buscarEquipoParaTarea(Long equipoId) {
		if (equipoId != null) {
			return buscarEquipoOpcional(equipoId);
		}
		return equipoRepository.findByNombreIgnoreCase(EQUIPO_GENERICO_NOMBRE)
				.orElseGet(() -> equipoRepository.save(new Equipo(EQUIPO_GENERICO_NOMBRE, "Sin fuero informado")));
	}

	private void validarExistencia(Long tareaId) {
		if (!tareaTecnicaRepository.existsById(tareaId)) {
			throw new TareaTecnicaNoEncontradaException(tareaId);
		}
	}

	private TareaTecnicaDetalle toDetalle(TareaTecnica tarea) {
		Equipo equipo = tarea.getEquipo();
		return new TareaTecnicaDetalle(
				tarea.getId(),
				equipo == null ? null : equipo.getId(),
				equipo == null ? null : equipo.getNombre(),
				tarea.getTitulo(),
				tarea.getDescripcion(),
				tarea.getSolicitanteUsername(),
				tarea.getSolicitanteNombre(),
				tarea.getSolicitanteFuero(),
				tarea.getEstado(),
				tarea.getPrioridad(),
				tarea.getResponsable(),
				tarea.getCreadoPor(),
				tarea.getObservacionesCierre(),
				tarea.getCreadoEn(),
				tarea.getCerradoEn());
	}

	private TareaComentarioDetalle toComentarioDetalle(TareaTecnicaComentario comentario) {
		return new TareaComentarioDetalle(
				comentario.getId(),
				comentario.getTarea().getId(),
				comentario.getAutor(),
				comentario.getComentario(),
				comentario.getCreadoEn());
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

	public record GuardarTareaTecnicaCommand(
			Long equipoId,
			String titulo,
			String descripcion,
			String solicitanteUsername,
			String solicitanteNombre,
			String solicitanteFuero,
			PrioridadTareaTecnica prioridad,
			String responsable,
			String creadoPor) {
	}

	public record CambiarEstadoTareaCommand(
			EstadoTareaTecnica estado,
			String observacionesCierre) {
	}

	public record AgregarComentarioTareaCommand(
			String autor,
			String comentario) {
	}

	public record TareaTecnicaDetalle(
			Long id,
			Long equipoId,
			String equipoNombre,
			String titulo,
			String descripcion,
			String solicitanteUsername,
			String solicitanteNombre,
			String solicitanteFuero,
			EstadoTareaTecnica estado,
			PrioridadTareaTecnica prioridad,
			String responsable,
			String creadoPor,
			String observacionesCierre,
			LocalDateTime creadoEn,
			LocalDateTime cerradoEn) {
	}

	public record TareaComentarioDetalle(
			Long id,
			Long tareaId,
			String autor,
			String comentario,
			LocalDateTime creadoEn) {
	}

	public static class TareaTecnicaNoEncontradaException extends RuntimeException {
		public TareaTecnicaNoEncontradaException(Long id) {
			super("Tarea tecnica no encontrada: " + id);
		}
	}

	public static class TareaTecnicaYaAsignadaException extends RuntimeException {
		public TareaTecnicaYaAsignadaException(Long id, String responsable) {
			super("Tarea tecnica " + id + " ya asignada a " + responsable + ".");
		}
	}

	public static class EquipoNoEncontradoException extends RuntimeException {
		public EquipoNoEncontradoException(Long id) {
			super("Equipo no encontrado: " + id);
		}
	}
}
