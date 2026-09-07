package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;
import java.util.Set;

import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.ActiveDirectoryDomainService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.ActiveDirectoryDomainService.DominioUsuarios;
import ar.gov.justiciajujuy.sanpedro.inventario.security.OrigenIdentidad;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.AutorizarUsuarioDominioCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.CrearUsuarioCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.PasswordLocalRequeridoException;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.RolNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.UsuarioDuplicadoException;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.UsuarioResumen;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/v1/usuarios")
public class UsuarioAdminController {

	private static final String MODULO_USUARIOS = "USUARIOS";
	private static final String PERMISO_ADMINISTRAR = "ADMINISTRAR";

	private final AuthorizationService authorizationService;
	private final ActiveDirectoryDomainService activeDirectoryDomainService;
	private final UsuarioManagementService usuarioManagementService;

	public UsuarioAdminController(
			AuthorizationService authorizationService,
			ActiveDirectoryDomainService activeDirectoryDomainService,
			UsuarioManagementService usuarioManagementService) {
		this.authorizationService = authorizationService;
		this.activeDirectoryDomainService = activeDirectoryDomainService;
		this.usuarioManagementService = usuarioManagementService;
	}

	@GetMapping
	public UsuariosResponse listarUsuarios(@AuthenticationPrincipal UserDetails userDetails) {
		exigirPermisoAdministrarUsuarios(userDetails);
		return new UsuariosResponse(usuarioManagementService.listarUsuarios());
	}

	@GetMapping("/dominio")
	public DominioUsuarios listarUsuariosDominio(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(name = "q", required = false) String query) {
		exigirPermisoAdministrarUsuarios(userDetails);
		return activeDirectoryDomainService.buscarUsuarios(query);
	}

	@PostMapping("/dominio")
	@ResponseStatus(HttpStatus.CREATED)
	public UsuarioResumen autorizarUsuarioDominio(
			@AuthenticationPrincipal UserDetails userDetails,
			@Valid @RequestBody AutorizarUsuarioDominioRequest request) {
		exigirPermisoAdministrarUsuarios(userDetails);
		return usuarioManagementService.autorizarUsuarioDominio(request.toCommand());
	}

	@PostMapping
	@ResponseStatus(HttpStatus.CREATED)
	public UsuarioResumen crearUsuario(
			@AuthenticationPrincipal UserDetails userDetails,
			@Valid @RequestBody CrearUsuarioRequest request) {
		exigirPermisoAdministrarUsuarios(userDetails);
		return usuarioManagementService.crearUsuario(request.toCommand());
	}

	@org.springframework.web.bind.annotation.PutMapping("/{id}")
	public UsuarioResumen actualizarUsuario(
			@AuthenticationPrincipal UserDetails userDetails,
			@org.springframework.web.bind.annotation.PathVariable Long id,
			@Valid @RequestBody ActualizarUsuarioRequest request) {
		exigirPermisoAdministrarUsuarios(userDetails);
		return usuarioManagementService.actualizarUsuario(id, request.roles(), request.activo());
	}

	@org.springframework.web.bind.annotation.PutMapping("/{id}/password")
	@ResponseStatus(HttpStatus.NO_CONTENT)
	public void cambiarPasswordLocal(
			@AuthenticationPrincipal UserDetails userDetails,
			@org.springframework.web.bind.annotation.PathVariable Long id,
			@Valid @RequestBody CambiarPasswordRequest request) {
		exigirPermisoAdministrarUsuarios(userDetails);
		usuarioManagementService.cambiarPasswordLocal(id, request.password());
	}

	private void exigirPermisoAdministrarUsuarios(UserDetails userDetails) {
		/*
		 * Spring Security ya confirmo la identidad. Esta verificacion confirma que el
		 * usuario tenga autorizacion local para administrar el modulo USUARIOS.
		 */
		if (!authorizationService.tienePermiso(userDetails, MODULO_USUARIOS, PERMISO_ADMINISTRAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para administrar usuarios.");
		}
	}

	@ExceptionHandler(UsuarioDuplicadoException.class)
	@ResponseStatus(HttpStatus.CONFLICT)
	void usuarioDuplicado() {
	}

	@ExceptionHandler(RolNoEncontradoException.class)
	@ResponseStatus(HttpStatus.UNPROCESSABLE_CONTENT)
	void rolNoEncontrado() {
	}

	@ExceptionHandler(PasswordLocalRequeridoException.class)
	@ResponseStatus(HttpStatus.UNPROCESSABLE_CONTENT)
	void passwordLocalRequerido() {
	}

	public record UsuariosResponse(List<UsuarioResumen> usuarios) {
	}

	public record CrearUsuarioRequest(
			@NotBlank
			@Size(max = 120)
			@Pattern(regexp = "^[a-zA-Z0-9._@-]+$")
			String username,

			@NotBlank
			@Size(max = 180)
			String nombreVisible,

			@NotBlank
			@Size(max = 120)
			String fuero,

			@Size(max = 20)
			String origen,

			@Size(max = 120)
			String password,

			boolean activo,

			@NotEmpty
			Set<@NotBlank @Size(max = 60) String> roles) {

		private CrearUsuarioCommand toCommand() {
			return new CrearUsuarioCommand(username, nombreVisible, fuero, OrigenIdentidad.LOCAL.name(), password, activo, roles);
		}
	}

	public record AutorizarUsuarioDominioRequest(
			@NotBlank
			@Size(max = 120)
			@Pattern(regexp = "^[a-zA-Z0-9._@-]+$")
			String username,

			@NotBlank
			@Size(max = 180)
			String nombreVisible,

			@NotBlank
			@Size(max = 120)
			String fuero,

			boolean activo,

			@NotEmpty
			Set<@NotBlank @Size(max = 60) String> roles) {

		private AutorizarUsuarioDominioCommand toCommand() {
			return new AutorizarUsuarioDominioCommand(username, nombreVisible, fuero, activo, roles);
		}
	}

	public record ActualizarUsuarioRequest(
			boolean activo,
			@NotEmpty
			Set<@NotBlank @Size(max = 60) String> roles) {
	}

	public record CambiarPasswordRequest(
			@NotBlank
			@Size(min = 8, max = 120)
			String password) {
	}
}
