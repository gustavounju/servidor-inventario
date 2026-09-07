package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.reportes.ReporteService;
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
public class ReportePageController {

	private static final String MODULO_REPORTES = "REPORTES";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EXPORTAR = "EXPORTAR";

	private final AuthorizationService authorizationService;
	private final ReporteService reporteService;

	public ReportePageController(AuthorizationService authorizationService, ReporteService reporteService) {
		this.authorizationService = authorizationService;
		this.reporteService = reporteService;
	}

	@GetMapping("/admin/reportes")
	public String reportes(Model model, @AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query) {
		exigirPermiso(userDetails, PERMISO_VER);
		model.addAttribute("resumen", reporteService.resumen());
		model.addAttribute("filtroQuery", query);
		model.addAttribute("puedeExportarReportes", authorizationService.tienePermiso(userDetails, MODULO_REPORTES, PERMISO_EXPORTAR));
		return "admin/reportes";
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_REPORTES, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar reportes.");
		}
	}
}
