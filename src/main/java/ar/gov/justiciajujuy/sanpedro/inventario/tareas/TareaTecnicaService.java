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
				buscarEquipoOpcional(command.equipoId()),
				textoRequerido(command.titulo(), "titulo"),
				textoOpcional(command.descripcion()),
				command.prioridad() == null ? PrioridadTareaTecnica.MEDIA : command.prioridad(),
				textoOpcional(command.responsable()));
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
				buscarEquipoOpcional(command.equipoId()),
				textoRequerido(command.titulo(), "titulo"),
				textoOpcional(command.descripcion()),
				command.prioridad() == null ? PrioridadTareaTecnica.MEDIA : command.prioridad(),
				textoOpcional(command.responsable()));
		auditoriaService.registrar("TAREAS", "ACTUALIZAR", "TareaTecnica", tarea.getId(),
				"Tarea tecnica " + tarea.getId() + " actualizada.");
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

	private Equipo buscarEquipoOpcional(Long equipoId) {
		if (equipoId == null) {
			return null;
		}
		return equipoRepository.findById(equipoId)
				.orElseThrow(() -> new EquipoNoEncontradoException(equipoId));
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
				tarea.getEstado(),
				tarea.getPrioridad(),
				tarea.getResponsable(),
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
			PrioridadTareaTecnica prioridad,
			String responsable) {
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
			EstadoTareaTecnica estado,
			PrioridadTareaTecnica prioridad,
			String responsable,
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

	public static class EquipoNoEncontradoException extends RuntimeException {
		public EquipoNoEncontradoException(Long id) {
			super("Equipo no encontrado: " + id);
		}
	}
}
