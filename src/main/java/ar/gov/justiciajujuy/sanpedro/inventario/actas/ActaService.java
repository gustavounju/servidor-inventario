package ar.gov.justiciajujuy.sanpedro.inventario.actas;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import ar.gov.justiciajujuy.sanpedro.inventario.auditoria.AuditoriaService;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.Equipo;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class ActaService {

	private final ActaRepository actaRepository;
	private final EquipoRepository equipoRepository;
	private final AuditoriaService auditoriaService;

	public ActaService(ActaRepository actaRepository, EquipoRepository equipoRepository,
			AuditoriaService auditoriaService) {
		this.actaRepository = actaRepository;
		this.equipoRepository = equipoRepository;
		this.auditoriaService = auditoriaService;
	}

	@Transactional(readOnly = true)
	public List<ActaDetalle> buscar(String query, TipoActa tipo, EstadoActa estado) {
		return actaRepository.buscar(textoOpcional(query), tipo, estado).stream()
				.map(this::toDetalle)
				.toList();
	}

	@Transactional(readOnly = true)
	public String proximoNumero(LocalDate fechaEmision) {
		return generarNumeroDisponible(fechaEmision == null ? LocalDate.now() : fechaEmision);
	}

	@Transactional
	public ActaDetalle crear(GuardarActaCommand command) {
		String numero = textoOpcional(command.numero());
		if (numero == null) {
			numero = generarNumeroDisponible(command.fechaEmision() == null ? LocalDate.now() : command.fechaEmision());
		}
		exigirNumeroDisponible(numero, null);
		Acta acta = new Acta(
				numero,
				command.tipo() == null ? TipoActa.ENTREGA : command.tipo(),
				textoRequerido(command.destinatario(), "destinatario"),
				textoRequerido(command.detalle(), "detalle"));
		aplicar(acta, command, numero);
		Acta guardada = actaRepository.save(acta);
		auditoriaService.registrar("ACTAS", "CREAR", "Acta", guardada.getId(),
				"Acta " + guardada.getNumero() + " creada.");
		return toDetalle(guardada);
	}

	@Transactional
	public ActaDetalle actualizar(Long id, GuardarActaCommand command) {
		Acta acta = actaRepository.findById(id).orElseThrow(() -> new ActaNoEncontradaException(id));
		exigirNumeroDisponible(textoRequerido(command.numero(), "numero"), id);
		aplicar(acta, command, textoRequerido(command.numero(), "numero"));
		Acta guardada = actaRepository.save(acta);
		auditoriaService.registrar("ACTAS", "ACTUALIZAR", "Acta", guardada.getId(),
				"Acta " + guardada.getNumero() + " actualizada.");
		return toDetalle(guardada);
	}

	public long contar() {
		return actaRepository.count();
	}

	private void aplicar(Acta acta, GuardarActaCommand command, String numero) {
		acta.actualizar(
				numero,
				command.tipo() == null ? TipoActa.ENTREGA : command.tipo(),
				equipoOpcional(command.equipoId()),
				command.fechaEmision(),
				textoRequerido(command.destinatario(), "destinatario"),
				textoOpcional(command.responsableEntrega()),
				textoOpcional(command.responsableRecepcion()),
				textoRequerido(command.detalle(), "detalle"),
				command.estado() == null ? EstadoActa.BORRADOR : command.estado(),
				textoOpcional(command.observaciones()),
				command.activo());
	}

	private Equipo equipoOpcional(Long equipoId) {
		if (equipoId == null) {
			return null;
		}
		return equipoRepository.findById(equipoId).orElseThrow(() -> new EquipoNoEncontradoParaActaException(equipoId));
	}

	private ActaDetalle toDetalle(Acta acta) {
		Equipo equipo = acta.getEquipo();
		return new ActaDetalle(
				acta.getId(),
				acta.getNumero(),
				acta.getTipo(),
				equipo == null ? null : equipo.getId(),
				equipo == null ? null : equipo.getNombre(),
				acta.getFechaEmision(),
				acta.getDestinatario(),
				acta.getResponsableEntrega(),
				acta.getResponsableRecepcion(),
				acta.getDetalle(),
				acta.getEstado(),
				acta.getObservaciones(),
				acta.isActivo());
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

	private void exigirNumeroDisponible(String numero, Long idActual) {
		actaRepository.findByNumeroIgnoreCase(numero)
				.filter(acta -> idActual == null || !acta.getId().equals(idActual))
				.ifPresent(acta -> {
					throw new ActaDuplicadaException(numero);
				});
	}

	private String generarNumeroDisponible(LocalDate fechaEmision) {
		String prefijo = "ACT-" + fechaEmision.getYear() + "-";
		int siguiente = actaRepository.findTop20ByNumeroStartingWithOrderByNumeroDesc(prefijo).stream()
				.map(Acta::getNumero)
				.map(numero -> numero.substring(prefijo.length()))
				.map(this::numeroEntero)
				.flatMap(Optional::stream)
				.max(Integer::compareTo)
				.orElse(0) + 1;
		String candidato = prefijo + String.format("%04d", siguiente);
		while (actaRepository.findByNumeroIgnoreCase(candidato).isPresent()) {
			siguiente++;
			candidato = prefijo + String.format("%04d", siguiente);
		}
		return candidato;
	}

	private Optional<Integer> numeroEntero(String valor) {
		try {
			return Optional.of(Integer.parseInt(valor));
		}
		catch (NumberFormatException ex) {
			return Optional.empty();
		}
	}

	public record GuardarActaCommand(String numero, TipoActa tipo, Long equipoId, LocalDate fechaEmision,
			String destinatario, String responsableEntrega, String responsableRecepcion, String detalle,
			EstadoActa estado, String observaciones, boolean activo) {
	}

	public record ActaDetalle(Long id, String numero, TipoActa tipo, Long equipoId, String equipoNombre,
			LocalDate fechaEmision, String destinatario, String responsableEntrega, String responsableRecepcion,
			String detalle, EstadoActa estado, String observaciones, boolean activo) {
	}

	public static class ActaNoEncontradaException extends RuntimeException {
		public ActaNoEncontradaException(Long id) {
			super("Acta no encontrada: " + id);
		}
	}

	public static class ActaDuplicadaException extends RuntimeException {
		public ActaDuplicadaException(String numero) {
			super("Ya existe un acta con numero: " + numero);
		}
	}

	public static class EquipoNoEncontradoParaActaException extends RuntimeException {
		public EquipoNoEncontradoParaActaException(Long id) {
			super("Equipo no encontrado para acta: " + id);
		}
	}
}
