package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.componentes.EstadoComparacion;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.GemeloDigitalService;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.GemeloDigitalService.DashboardDiferencias;
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
@RequestMapping("/api/v1/gemelo-digital")
public class DashboardDiferenciasController {

	private static final String MODULO_COMPONENTES = "COMPONENTES";
	private static final String PERMISO_VER = "VER";

	private final AuthorizationService authorizationService;
	private final GemeloDigitalService gemeloDigitalService;

	public DashboardDiferenciasController(AuthorizationService authorizationService,
			GemeloDigitalService gemeloDigitalService) {
		this.authorizationService = authorizationService;
		this.gemeloDigitalService = gemeloDigitalService;
	}

	@GetMapping("/dashboard-diferencias")
	public DashboardDiferencias dashboard(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String equipo,
			@RequestParam(required = false) String fuero,
			@RequestParam(required = false) EstadoComparacion estado) {
		exigirPermiso(userDetails);
		return gemeloDigitalService.dashboardDiferencias(equipo, fuero, estado);
	}

	@GetMapping(value = "/dashboard-diferencias.csv", produces = "text/csv")
	public ResponseEntity<String> dashboardCsv(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String equipo,
			@RequestParam(required = false) String fuero,
			@RequestParam(required = false) EstadoComparacion estado) {
		exigirPermiso(userDetails);
		return ResponseEntity.ok()
				.contentType(MediaType.parseMediaType("text/csv; charset=UTF-8"))
				.header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"dashboard-diferencias.csv\"")
				.body(gemeloDigitalService.dashboardDiferenciasCsv(equipo, fuero, estado));
	}

	private void exigirPermiso(UserDetails userDetails) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, PERMISO_VER)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para ver diferencias del gemelo digital.");
		}
	}
}
