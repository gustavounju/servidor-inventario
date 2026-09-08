package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.config.SiteAvailabilityService;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.server.ResponseStatusException;

import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;

@Controller
public class SiteAdminController {

	private static final String MODULO_USUARIOS = "USUARIOS";
	private static final String PERMISO_ADMINISTRAR = "ADMINISTRAR";

	private final AuthorizationService authorizationService;
	private final SiteAvailabilityService siteAvailabilityService;

	public SiteAdminController(
			AuthorizationService authorizationService,
			SiteAvailabilityService siteAvailabilityService) {
		this.authorizationService = authorizationService;
		this.siteAvailabilityService = siteAvailabilityService;
	}

	@GetMapping("/admin/sitio")
	public String siteStatus(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(value = "updated", required = false) String updated,
			Model model) {
		requireSiteAdministration(userDetails);
		model.addAttribute("siteAvailability", siteAvailabilityService.current());
		model.addAttribute("updated", updated != null);
		return "admin/sitio";
	}

	@PostMapping("/admin/sitio")
	public String updateSiteStatus(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(value = "temporarilyInactive", defaultValue = "false") boolean temporarilyInactive,
			@RequestParam(value = "message", required = false) String message,
			@RequestParam(value = "allowedUsername", required = false) String allowedUsername) {
		requireSiteAdministration(userDetails);
		siteAvailabilityService.update(temporarilyInactive, message, allowedUsername);
		return "redirect:/admin/sitio?updated=true";
	}

	private void requireSiteAdministration(UserDetails userDetails) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_USUARIOS, PERMISO_ADMINISTRAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para administrar el sitio.");
		}
	}
}
