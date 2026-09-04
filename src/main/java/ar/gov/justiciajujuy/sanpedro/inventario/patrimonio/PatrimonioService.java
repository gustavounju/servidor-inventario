package ar.gov.justiciajujuy.sanpedro.inventario.patrimonio;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.auditoria.AuditoriaService;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.Equipo;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class PatrimonioService {

	private final BienPatrimonialRepository bienPatrimonialRepository;
	private final EquipoRepository equipoRepository;
	private final AuditoriaService auditoriaService;

	public PatrimonioService(BienPatrimonialRepository bienPatrimonialRepository, EquipoRepository equipoRepository,
			AuditoriaService auditoriaService) {
		this.bienPatrimonialRepository = bienPatrimonialRepository;
		this.equipoRepository = equipoRepository;
		this.auditoriaService = auditoriaService;
	}

	@Transactional(readOnly = true)
	public List<BienPatrimonialDetalle> buscar(String query, EstadoBienPatrimonial estado) {
		return bienPatrimonialRepository.buscar(textoOpcional(query), estado).stream()
				.map(this::toDetalle)
				.toList();
	}

	@Transactional
	public BienPatrimonialDetalle crear(GuardarBienPatrimonialCommand command) {
		String numeroPatrimonial = textoRequerido(command.numeroPatrimonial(), "numeroPatrimonial");
		exigirNumeroDisponible(numeroPatrimonial, null);
		BienPatrimonial bien = new BienPatrimonial(
				numeroPatrimonial,
				textoRequerido(command.categoria(), "categoria"),
				textoRequerido(command.descripcion(), "descripcion"));
		aplicar(bien, command);
		BienPatrimonial guardado = bienPatrimonialRepository.save(bien);
		auditoriaService.registrar("PATRIMONIO", "CREAR", "BienPatrimonial", guardado.getId(),
				"Bien patrimonial " + guardado.getNumeroPatrimonial() + " creado.");
		return toDetalle(guardado);
	}

	@Transactional
	public BienPatrimonialDetalle actualizar(Long id, GuardarBienPatrimonialCommand command) {
		BienPatrimonial bien = bienPatrimonialRepository.findById(id)
				.orElseThrow(() -> new BienPatrimonialNoEncontradoException(id));
		exigirNumeroDisponible(textoRequerido(command.numeroPatrimonial(), "numeroPatrimonial"), id);
		aplicar(bien, command);
		BienPatrimonial guardado = bienPatrimonialRepository.save(bien);
		auditoriaService.registrar("PATRIMONIO", "ACTUALIZAR", "BienPatrimonial", guardado.getId(),
				"Bien patrimonial " + guardado.getNumeroPatrimonial() + " actualizado.");
		return toDetalle(guardado);
	}

	@Transactional
	public void eliminar(Long id) {
		BienPatrimonial bien = bienPatrimonialRepository.findById(id)
				.orElseThrow(() -> new BienPatrimonialNoEncontradoException(id));
		String num = bien.getNumeroPatrimonial();
		bienPatrimonialRepository.delete(bien);
		auditoriaService.registrar("PATRIMONIO", "ELIMINAR", "BienPatrimonial", id,
				"Bien patrimonial " + num + " eliminado.");
	}

	public long contar() {
		return bienPatrimonialRepository.count();
	}

	private void aplicar(BienPatrimonial bien, GuardarBienPatrimonialCommand command) {
		bien.actualizar(
				textoRequerido(command.numeroPatrimonial(), "numeroPatrimonial"),
				textoRequerido(command.categoria(), "categoria"),
				textoRequerido(command.descripcion(), "descripcion"),
				textoOpcional(command.ubicacion()),
				textoOpcional(command.fuero()),
				textoOpcional(command.custodio()),
				command.estado() == null ? EstadoBienPatrimonial.EN_USO : command.estado(),
				buscarEquipoOpcional(command.equipoId()),
				textoOpcional(command.observaciones()),
				command.activo());
	}

	private Equipo buscarEquipoOpcional(Long equipoId) {
		if (equipoId == null) {
			return null;
		}
		return equipoRepository.findById(equipoId).orElseThrow(() -> new EquipoNoEncontradoException(equipoId));
	}

	private BienPatrimonialDetalle toDetalle(BienPatrimonial bien) {
		Equipo equipo = bien.getEquipo();
		return new BienPatrimonialDetalle(
				bien.getId(),
				bien.getNumeroPatrimonial(),
				bien.getCategoria(),
				bien.getDescripcion(),
				bien.getUbicacion(),
				bien.getFuero(),
				bien.getCustodio(),
				bien.getEstado(),
				equipo == null ? null : equipo.getId(),
				equipo == null ? null : equipo.getNombre(),
				bien.getObservaciones(),
				bien.isActivo());
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

	private void exigirNumeroDisponible(String numeroPatrimonial, Long idActual) {
		bienPatrimonialRepository.findByNumeroPatrimonialIgnoreCase(numeroPatrimonial)
				.filter(bien -> idActual == null || !bien.getId().equals(idActual))
				.ifPresent(bien -> {
					throw new BienPatrimonialDuplicadoException(numeroPatrimonial);
				});
	}

	public record GuardarBienPatrimonialCommand(String numeroPatrimonial, String categoria, String descripcion,
			String ubicacion, String fuero, String custodio, EstadoBienPatrimonial estado, Long equipoId,
			String observaciones, boolean activo) {
	}

	public record BienPatrimonialDetalle(Long id, String numeroPatrimonial, String categoria, String descripcion,
			String ubicacion, String fuero, String custodio, EstadoBienPatrimonial estado, Long equipoId,
			String equipoNombre, String observaciones, boolean activo) {
	}

	public static class BienPatrimonialNoEncontradoException extends RuntimeException {
		public BienPatrimonialNoEncontradoException(Long id) {
			super("Bien patrimonial no encontrado: " + id);
		}
	}

	public static class BienPatrimonialDuplicadoException extends RuntimeException {
		public BienPatrimonialDuplicadoException(String numeroPatrimonial) {
			super("Ya existe un bien patrimonial con numero: " + numeroPatrimonial);
		}
	}

	public static class EquipoNoEncontradoException extends RuntimeException {
		public EquipoNoEncontradoException(Long id) {
			super("Equipo no encontrado: " + id);
		}
	}
}
