package ar.gov.justiciajujuy.sanpedro.inventario.auditoria;

import java.time.LocalDateTime;
import java.util.List;
import java.io.ByteArrayOutputStream;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import ar.gov.justiciajujuy.sanpedro.inventario.equipos.Equipo;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import org.thymeleaf.context.Context;
import org.thymeleaf.spring6.SpringTemplateEngine;
import org.xhtmlrenderer.pdf.ITextRenderer;

@Service
public class AuditoriaService {

	private static final int DETALLE_MAXIMO = 1000;

	private final AuditoriaEventoRepository auditoriaEventoRepository;
    private final MovimientoEquipoRepository movimientoRepository;
    private final EquipoRepository equipoRepository;
    private final SpringTemplateEngine templateEngine;

	public AuditoriaService(AuditoriaEventoRepository auditoriaEventoRepository,
                            MovimientoEquipoRepository movimientoRepository,
                            EquipoRepository equipoRepository,
                            SpringTemplateEngine templateEngine) {
		this.auditoriaEventoRepository = auditoriaEventoRepository;
        this.movimientoRepository = movimientoRepository;
        this.equipoRepository = equipoRepository;
        this.templateEngine = templateEngine;
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

    @Transactional(readOnly = true)
    public List<MovimientoEquipo> obtenerHistorial(Long equipoId) {
        return movimientoRepository.findByEquipoIdOrderByFechaMovimientoDesc(equipoId);
    }

    @Transactional
    public MovimientoEquipo registrarMovimiento(Long equipoId, TipoMovimiento tipo, String usuarioDestino, String ubiOrigen, String ubiDestino, String admin, String obs) {
        Equipo equipo = equipoRepository.findById(equipoId)
            .orElseThrow(() -> new IllegalArgumentException("Equipo no encontrado"));
        
        MovimientoEquipo mov = new MovimientoEquipo(equipo, tipo, usuarioDestino, ubiOrigen, ubiDestino, admin, obs);
        return movimientoRepository.save(mov);
    }

    public byte[] generarActaPdf(Long movimientoId) throws Exception {
        MovimientoEquipo mov = movimientoRepository.findById(movimientoId)
            .orElseThrow(() -> new IllegalArgumentException("Movimiento no encontrado"));

        Context context = new Context();
        context.setVariable("movimiento", mov);
        context.setVariable("equipo", mov.getEquipo());
        
        String html = templateEngine.process("pdf/acta-movimiento", context);

        try (ByteArrayOutputStream os = new ByteArrayOutputStream()) {
            ITextRenderer renderer = new ITextRenderer();
            renderer.setDocumentFromString(html);
            renderer.layout();
            renderer.createPDF(os);
            return os.toByteArray();
        }
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
