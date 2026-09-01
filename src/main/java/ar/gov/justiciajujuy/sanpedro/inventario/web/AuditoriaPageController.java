package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.auditoria.AuditoriaService;
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
public class AuditoriaPageController {

	private static final String MODULO_AUDITORIA = "AUDITORIA";
	private static final String PERMISO_VER = "VER";

	private final AuthorizationService authorizationService;
	private final AuditoriaService auditoriaService;

	public AuditoriaPageController(AuthorizationService authorizationService, AuditoriaService auditoriaService) {
		this.authorizationService = authorizationService;
		this.auditoriaService = auditoriaService;
	}

	@GetMapping("/admin/auditoria")
	public String auditoria(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String usuario,
			@RequestParam(required = false) String modulo,
			@RequestParam(required = false) String accion) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_AUDITORIA, PERMISO_VER)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para ver auditoria.");
		}
		model.addAttribute("eventos", auditoriaService.buscar(usuario, modulo, accion));
		model.addAttribute("usuarioFiltro", usuario);
		model.addAttribute("moduloFiltro", modulo);
		model.addAttribute("accionFiltro", accion);
		return "admin/auditoria";
	}
}
