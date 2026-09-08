package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.config.SiteAvailabilityService;
import ar.gov.justiciajujuy.sanpedro.inventario.config.SiteAvailabilityService.SiteAvailability;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class LoginController {

	private final String applicationName;
	private final SiteAvailabilityService siteAvailabilityService;

	public LoginController(
			@Value("${spring.application.name}") String applicationName,
			SiteAvailabilityService siteAvailabilityService) {
		this.applicationName = applicationName;
		this.siteAvailabilityService = siteAvailabilityService;
	}

	@GetMapping("/login")
	public String login(
			@RequestParam(value = "error", required = false) String error,
			@RequestParam(value = "logout", required = false) String logout,
			@RequestParam(value = "inactive", required = false) String inactive,
			Model model) {
		SiteAvailability availability = siteAvailabilityService.current();
		model.addAttribute("applicationName", applicationName);
		model.addAttribute("hasError", error != null);
		model.addAttribute("loggedOut", logout != null);
		model.addAttribute("blockedByMaintenance", inactive != null);
		model.addAttribute("siteAvailability", availability);
		return "login";
	}
}
