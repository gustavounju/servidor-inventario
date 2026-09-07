package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.RolResumen;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/v1/roles")
public class RolAdminController {

	private static final String MODULO_USUARIOS = "USUARIOS";
	private static final String PERMISO_ADMINISTRAR = "ADMINISTRAR";

	private final AuthorizationService authorizationService;
	private final UsuarioManagementService usuarioManagementService;

	public RolAdminController(
			AuthorizationService authorizationService,
			UsuarioManagementService usuarioManagementService) {
		this.authorizationService = authorizationService;
		this.usuarioManagementService = usuarioManagementService;
	}

	@GetMapping
	public RolesResponse listarRoles(@AuthenticationPrincipal UserDetails userDetails) {
		/*
		 * Listar roles tambien es administracion de seguridad. Por eso se protege con
		 * el mismo permiso que la gestion de usuarios.
		 */
		if (!authorizationService.tienePermiso(userDetails, MODULO_USUARIOS, PERMISO_ADMINISTRAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para administrar roles.");
		}
		return new RolesResponse(usuarioManagementService.listarRoles());
	}

	public record RolesResponse(List<RolResumen> roles) {
	}
}
