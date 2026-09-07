package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.componentes.EstadoComparacion;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.GemeloDigitalService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.server.ResponseStatusException;

@Controller
public class DashboardDiferenciasPageController {

	private static final String MODULO_COMPONENTES = "COMPONENTES";
	private static final String PERMISO_VER = "VER";

	private final AuthorizationService authorizationService;
	private final GemeloDigitalService gemeloDigitalService;

	public DashboardDiferenciasPageController(AuthorizationService authorizationService,
			GemeloDigitalService gemeloDigitalService) {
		this.authorizationService = authorizationService;
		this.gemeloDigitalService = gemeloDigitalService;
	}

	@GetMapping("/admin/dashboard-diferencias")
	public String dashboard(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String equipo,
			@RequestParam(required = false) String fuero,
			@RequestParam(required = false) EstadoComparacion estado) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, PERMISO_VER)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para ver diferencias del gemelo digital.");
		}
		model.addAttribute("dashboard", gemeloDigitalService.dashboardDiferencias(equipo, fuero, estado));
		model.addAttribute("equipoFiltro", equipo);
		model.addAttribute("fueroFiltro", fuero);
		model.addAttribute("estadoFiltro", estado);
		model.addAttribute("estadosComparacion", EstadoComparacion.values());
		return "admin/dashboard-diferencias";
	}
}
