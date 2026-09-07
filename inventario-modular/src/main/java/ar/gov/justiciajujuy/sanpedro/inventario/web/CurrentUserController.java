package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService.ModuloAutorizado;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService.UsuarioActual;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/me")
public class CurrentUserController {

	private final AuthorizationService authorizationService;

	public CurrentUserController(AuthorizationService authorizationService) {
		this.authorizationService = authorizationService;
	}

	@GetMapping
	public UsuarioActual currentUser(@AuthenticationPrincipal UserDetails userDetails) {
		return authorizationService.obtenerUsuarioActual(userDetails);
	}

	@GetMapping("/modulos")
	public List<ModuloAutorizado> currentUserModules(@AuthenticationPrincipal UserDetails userDetails) {
		return authorizationService.obtenerUsuarioActual(userDetails).modulos();
	}
}
