package ar.gov.justiciajujuy.sanpedro.inventario.auditoria;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class AuditoriaService {

	private static final int DETALLE_MAXIMO = 1000;

	private final AuditoriaEventoRepository auditoriaEventoRepository;

	public AuditoriaService(AuditoriaEventoRepository auditoriaEventoRepository) {
		this.auditoriaEventoRepository = auditoriaEventoRepository;
	}

	@Transactional(readOnly = true)
	public List<AuditoriaEventoDetalle> listarRecientes() {
		return auditoriaEventoRepository.findTop100ByOrderByIdDesc().stream()
				.map(this::toDetalle)
				.toList();
	}

	@Transactional(readOnly = true)
	public List<AuditoriaEventoDetalle> buscar(String usuario, String modulo, String accion) {
		return auditoriaEventoRepository.filtrarRecientes(
				filtroFlexible(usuario),
				filtroExacto(modulo),
				filtroExacto(accion)).stream()
				.map(this::toDetalle)
				.toList();
	}

	@Transactional(readOnly = true)
	public String eventosCsv(String usuario, String modulo, String accion) {
		StringBuilder csv = new StringBuilder("id,fecha,usuario,modulo,accion,entidadTipo,entidadId,detalle\n");
		for (AuditoriaEventoDetalle evento : buscar(usuario, modulo, accion)) {
			csv.append(fila(List.of(
					String.valueOf(evento.id()),
					evento.creadoEn() == null ? "" : String.valueOf(evento.creadoEn()),
					evento.usuario(),
					evento.modulo(),
					evento.accion(),
					evento.entidadTipo(),
					evento.entidadId() == null ? "" : String.valueOf(evento.entidadId()),
					evento.detalle())));
		}
		return csv.toString();
	}

	@Transactional
	public void registrar(String modulo, String accion, String entidadTipo, Long entidadId, String detalle) {
		auditoriaEventoRepository.save(new AuditoriaEvento(
				usuarioActual(),
				textoRequerido(modulo, "SISTEMA"),
				textoRequerido(accion, "CAMBIO"),
				textoRequerido(entidadTipo, "REGISTRO"),
				entidadId,
				recortar(textoRequerido(detalle, "Cambio registrado."))));
	}

	private AuditoriaEventoDetalle toDetalle(AuditoriaEvento evento) {
		return new AuditoriaEventoDetalle(
				evento.getId(),
				evento.getUsuario(),
				evento.getModulo(),
				evento.getAccion(),
				evento.getEntidadTipo(),
				evento.getEntidadId(),
				evento.getDetalle(),
				evento.getCreadoEn());
	}

	private String usuarioActual() {
		Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
		if (authentication == null || authentication.getPrincipal() == null) {
			return "SISTEMA";
		}
		Object principal = authentication.getPrincipal();
		if (principal instanceof UserDetails userDetails) {
			return userDetails.getUsername();
		}
		return authentication.getName();
	}

	private String textoRequerido(String valor, String fallback) {
		return StringUtils.hasText(valor) ? valor.trim() : fallback;
	}

	private String recortar(String valor) {
		return valor.length() <= DETALLE_MAXIMO ? valor : valor.substring(0, DETALLE_MAXIMO);
	}

	private String filtroFlexible(String valor) {
		return StringUtils.hasText(valor) ? valor.trim() : null;
	}

	private String filtroExacto(String valor) {
		return StringUtils.hasText(valor) ? valor.trim().toUpperCase() : null;
	}

	private String fila(List<String> valores) {
		return valores.stream()
				.map(this::csv)
				.reduce((a, b) -> a + "," + b)
				.orElse("") + "\n";
	}

	private String csv(String valor) {
		String limpio = valor == null ? "" : valor.replace("\"", "\"\"");
		return limpio.contains(",") || limpio.contains("\"") || limpio.contains("\n") ? "\"" + limpio + "\"" : limpio;
	}

	public record AuditoriaEventoDetalle(
			Long id,
			String usuario,
			String modulo,
			String accion,
			String entidadTipo,
			Long entidadId,
			String detalle,
			LocalDateTime creadoEn) {
	}
}
