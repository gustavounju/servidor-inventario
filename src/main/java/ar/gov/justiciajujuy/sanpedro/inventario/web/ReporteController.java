package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.reportes.ReporteService;
import ar.gov.justiciajujuy.sanpedro.inventario.reportes.ReporteService.ResumenOperativo;
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
@RequestMapping("/api/v1/reportes")
public class ReporteController {

	private static final String MODULO_REPORTES = "REPORTES";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EXPORTAR = "EXPORTAR";

	private final AuthorizationService authorizationService;
	private final ReporteService reporteService;

	public ReporteController(AuthorizationService authorizationService, ReporteService reporteService) {
		this.authorizationService = authorizationService;
		this.reporteService = reporteService;
	}

	@GetMapping("/resumen")
	public ResumenOperativo resumen(@AuthenticationPrincipal UserDetails userDetails) {
		exigirPermiso(userDetails, PERMISO_VER);
		return reporteService.resumen();
	}

	@GetMapping(value = "/muebles.csv", produces = "text/csv")
	public ResponseEntity<String> mueblesCsv(@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query) {
		exigirPermiso(userDetails, PERMISO_EXPORTAR);
		return csv("muebles.csv", reporteService.mueblesCsv(query));
	}

	@GetMapping(value = "/patrimonio.csv", produces = "text/csv")
	public ResponseEntity<String> patrimonioCsv(@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query) {
		exigirPermiso(userDetails, PERMISO_EXPORTAR);
		return csv("patrimonio.csv", reporteService.patrimonioCsv(query));
	}

	@GetMapping(value = "/tareas.csv", produces = "text/csv")
	public ResponseEntity<String> tareasCsv(@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query) {
		exigirPermiso(userDetails, PERMISO_EXPORTAR);
		return csv("tareas.csv", reporteService.tareasCsv(query));
	}

	@GetMapping(value = "/actas.csv", produces = "text/csv")
	public ResponseEntity<String> actasCsv(@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query) {
		exigirPermiso(userDetails, PERMISO_EXPORTAR);
		return csv("actas.csv", reporteService.actasCsv(query));
	}

	@GetMapping(value = "/ubicaciones.csv", produces = "text/csv")
	public ResponseEntity<String> ubicacionesCsv(@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query) {
		exigirPermiso(userDetails, PERMISO_EXPORTAR);
		return csv("ubicaciones.csv", reporteService.ubicacionesCsv(query));
	}

	private ResponseEntity<String> csv(String nombre, String contenido) {
		return ResponseEntity.ok()
				.contentType(MediaType.parseMediaType("text/csv; charset=UTF-8"))
				.header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + nombre + "\"")
				.body(contenido);
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_REPORTES, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar reportes.");
		}
	}
}
