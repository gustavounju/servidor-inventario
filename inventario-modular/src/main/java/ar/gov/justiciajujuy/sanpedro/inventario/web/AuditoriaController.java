package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.auditoria.AuditoriaService;
import ar.gov.justiciajujuy.sanpedro.inventario.auditoria.AuditoriaService.AuditoriaEventoDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/v1/auditoria")
public class AuditoriaController {

	private static final String MODULO_AUDITORIA = "AUDITORIA";
	private static final String PERMISO_VER = "VER";

	private final AuthorizationService authorizationService;
	private final AuditoriaService auditoriaService;

	public AuditoriaController(AuthorizationService authorizationService, AuditoriaService auditoriaService) {
		this.authorizationService = authorizationService;
		this.auditoriaService = auditoriaService;
	}

	@GetMapping("/eventos")
	public List<AuditoriaEventoDetalle> listar(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String usuario,
			@RequestParam(required = false) String modulo,
			@RequestParam(required = false) String accion) {
		exigirPermiso(userDetails);
		return auditoriaService.buscar(usuario, modulo, accion);
	}

	@GetMapping(value = "/eventos.csv", produces = "text/csv")
	public ResponseEntity<String> eventosCsv(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String usuario,
			@RequestParam(required = false) String modulo,
			@RequestParam(required = false) String accion) {
		exigirPermiso(userDetails);
		return ResponseEntity.ok()
				.contentType(MediaType.parseMediaType("text/csv; charset=UTF-8"))
				.header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"auditoria-eventos.csv\"")
				.body(auditoriaService.eventosCsv(usuario, modulo, accion));
	}

	private void exigirPermiso(UserDetails userDetails) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_AUDITORIA, PERMISO_VER)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para ver auditoria.");
		}
	}
}
