package ar.gov.justiciajujuy.sanpedro.inventario.web;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class LoginController {

	private final String applicationName;

	public LoginController(@Value("${spring.application.name}") String applicationName) {
		this.applicationName = applicationName;
	}

	@GetMapping("/login")
	public String login(
			@RequestParam(value = "error", required = false) String error,
			@RequestParam(value = "logout", required = false) String logout,
			Model model) {
		model.addAttribute("applicationName", applicationName);
		model.addAttribute("hasError", error != null);
		model.addAttribute("loggedOut", logout != null);
		return "login";
	}
}
