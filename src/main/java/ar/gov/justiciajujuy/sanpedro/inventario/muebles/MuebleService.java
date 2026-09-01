package ar.gov.justiciajujuy.sanpedro.inventario.muebles;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.auditoria.AuditoriaService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class MuebleService {

	private final MuebleRepository muebleRepository;
	private final AuditoriaService auditoriaService;

	public MuebleService(MuebleRepository muebleRepository, AuditoriaService auditoriaService) {
		this.muebleRepository = muebleRepository;
		this.auditoriaService = auditoriaService;
	}

	@Transactional(readOnly = true)
	public List<MuebleDetalle> buscar(String query, EstadoMueble estado) {
		return muebleRepository.buscar(textoOpcional(query), estado).stream()
				.map(this::toDetalle)
				.toList();
	}

	@Transactional
	public MuebleDetalle crear(GuardarMuebleCommand command) {
		String codigo = textoRequerido(command.codigo(), "codigo");
		exigirCodigoDisponible(codigo, null);
		Mueble mueble = new Mueble(
				codigo,
				textoRequerido(command.tipo(), "tipo"),
				textoRequerido(command.descripcion(), "descripcion"));
		aplicar(mueble, command);
		Mueble guardado = muebleRepository.save(mueble);
		auditoriaService.registrar("MUEBLES", "CREAR", "Mueble", guardado.getId(),
				"Mueble " + guardado.getCodigo() + " creado.");
		return toDetalle(guardado);
	}

	@Transactional
	public MuebleDetalle actualizar(Long id, GuardarMuebleCommand command) {
		Mueble mueble = muebleRepository.findById(id).orElseThrow(() -> new MuebleNoEncontradoException(id));
		exigirCodigoDisponible(textoRequerido(command.codigo(), "codigo"), id);
		aplicar(mueble, command);
		Mueble guardado = muebleRepository.save(mueble);
		auditoriaService.registrar("MUEBLES", "ACTUALIZAR", "Mueble", guardado.getId(),
				"Mueble " + guardado.getCodigo() + " actualizado.");
		return toDetalle(guardado);
	}

	public long contar() {
		return muebleRepository.count();
	}

	private void aplicar(Mueble mueble, GuardarMuebleCommand command) {
		mueble.actualizar(
				textoRequerido(command.codigo(), "codigo"),
				textoRequerido(command.tipo(), "tipo"),
				textoRequerido(command.descripcion(), "descripcion"),
				textoOpcional(command.ubicacion()),
				textoOpcional(command.fuero()),
				textoOpcional(command.responsable()),
				command.estado() == null ? EstadoMueble.ACTIVO : command.estado(),
				textoOpcional(command.observaciones()),
				command.activo());
	}

	private MuebleDetalle toDetalle(Mueble mueble) {
		return new MuebleDetalle(
				mueble.getId(),
				mueble.getCodigo(),
				mueble.getTipo(),
				mueble.getDescripcion(),
				mueble.getUbicacion(),
				mueble.getFuero(),
				mueble.getResponsable(),
				mueble.getEstado(),
				mueble.getObservaciones(),
				mueble.isActivo());
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
		muebleRepository.findByCodigoIgnoreCase(codigo)
				.filter(mueble -> idActual == null || !mueble.getId().equals(idActual))
				.ifPresent(mueble -> {
					throw new MuebleDuplicadoException(codigo);
				});
	}

	public record GuardarMuebleCommand(String codigo, String tipo, String descripcion, String ubicacion, String fuero,
			String responsable, EstadoMueble estado, String observaciones, boolean activo) {
	}

	public record MuebleDetalle(Long id, String codigo, String tipo, String descripcion, String ubicacion,
			String fuero, String responsable, EstadoMueble estado, String observaciones, boolean activo) {
	}

	public static class MuebleNoEncontradoException extends RuntimeException {
		public MuebleNoEncontradoException(Long id) {
			super("Mueble no encontrado: " + id);
		}
	}

	public static class MuebleDuplicadoException extends RuntimeException {
		public MuebleDuplicadoException(String codigo) {
			super("Ya existe un mueble con codigo: " + codigo);
		}
	}
}
