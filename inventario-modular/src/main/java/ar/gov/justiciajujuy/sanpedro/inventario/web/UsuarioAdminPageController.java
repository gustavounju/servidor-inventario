package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.Set;

import ar.gov.justiciajujuy.sanpedro.inventario.security.ActiveDirectoryDomainService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.OrigenIdentidad;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.AutorizarUsuarioDominioCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.CrearUsuarioCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.PasswordLocalRequeridoException;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.RolNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.UsuarioDuplicadoException;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.server.ResponseStatusException;

@Controller
public class UsuarioAdminPageController {

	private static final String MODULO_USUARIOS = "USUARIOS";
	private static final String PERMISO_ADMINISTRAR = "ADMINISTRAR";

	private final AuthorizationService authorizationService;
	private final ActiveDirectoryDomainService activeDirectoryDomainService;
	private final UsuarioManagementService usuarioManagementService;

	public UsuarioAdminPageController(
			AuthorizationService authorizationService,
			ActiveDirectoryDomainService activeDirectoryDomainService,
			UsuarioManagementService usuarioManagementService) {
		this.authorizationService = authorizationService;
		this.activeDirectoryDomainService = activeDirectoryDomainService;
		this.usuarioManagementService = usuarioManagementService;
	}

	@GetMapping("/admin/usuarios")
	public String usuarios(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(name = "q", required = false) String query) {
		exigirPermisoAdministrarUsuarios(userDetails);
		cargarModelo(model, query);
		return "admin/usuarios";
	}

	@PostMapping("/admin/usuarios")
	public String crearUsuario(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam String username,
			@RequestParam String nombreVisible,
			@RequestParam String fuero,
			@RequestParam(required = false) String password,
			@RequestParam(defaultValue = "false") boolean activo,
			@RequestParam Set<String> roles) {
		exigirPermisoAdministrarUsuarios(userDetails);

		String usernameNormalizado = username.trim().toLowerCase();
		try {
			usuarioManagementService.crearUsuario(new CrearUsuarioCommand(
					username,
					nombreVisible,
					fuero,
					OrigenIdentidad.LOCAL.name(),
					password,
					activo,
					roles));
			return "redirect:/admin/usuarios?creado=" + usernameNormalizado;
		} catch (UsuarioDuplicadoException exception) {
			return "redirect:/admin/usuarios?error=duplicado";
		} catch (RolNoEncontradoException exception) {
			return "redirect:/admin/usuarios?error=rol";
		} catch (PasswordLocalRequeridoException exception) {
			return "redirect:/admin/usuarios?error=password";
		}
	}

	@PostMapping("/admin/usuarios/dominio")
	public String autorizarUsuarioDominio(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam String username,
			@RequestParam String nombreVisible,
			@RequestParam String fuero,
			@RequestParam(defaultValue = "true") boolean activo,
			@RequestParam Set<String> roles) {
		exigirPermisoAdministrarUsuarios(userDetails);

		String usernameNormalizado = username.trim().toLowerCase();
		try {
			usuarioManagementService.autorizarUsuarioDominio(new AutorizarUsuarioDominioCommand(
					username,
					nombreVisible,
					fuero,
					activo,
					roles));
			return "redirect:/admin/usuarios?q=" + usernameNormalizado + "&autorizado=" + usernameNormalizado;
		} catch (UsuarioDuplicadoException exception) {
			return "redirect:/admin/usuarios?error=duplicado";
		} catch (RolNoEncontradoException exception) {
			return "redirect:/admin/usuarios?error=rol";
		}
	}

	private void cargarModelo(Model model, String query) {
		model.addAttribute("usuarios", usuarioManagementService.listarUsuarios());
		model.addAttribute("usuariosDominio", activeDirectoryDomainService.buscarUsuarios(query));
		model.addAttribute("roles", usuarioManagementService.listarRoles());
	}

	@PostMapping("/admin/usuarios/editar")
	public String editarUsuario(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam Long id,
			@RequestParam(defaultValue = "false") boolean activo,
			@RequestParam(required = false) Set<String> roles) {
		exigirPermisoAdministrarUsuarios(userDetails);
		if (roles == null) {
			roles = Set.of();
		}
		try {
			usuarioManagementService.actualizarUsuario(id, roles, activo);
			return "redirect:/admin/usuarios?actualizado=true";
		} catch (RolNoEncontradoException exception) {
			return "redirect:/admin/usuarios?error=rol";
		}
	}

	@PostMapping("/admin/usuarios/cambiar-clave")
	public String cambiarClave(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam Long id,
			@RequestParam String password) {
		exigirPermisoAdministrarUsuarios(userDetails);
		try {
			usuarioManagementService.cambiarPasswordLocal(id, password);
			return "redirect:/admin/usuarios?claveCambiada=true";
		} catch (PasswordLocalRequeridoException exception) {
			return "redirect:/admin/usuarios?error=password";
		}
	}

	private void exigirPermisoAdministrarUsuarios(UserDetails userDetails) {
		/*
		 * La pantalla permite cambiar autorizaciones. Por eso no alcanza con estar
		 * autenticado: el usuario debe tener ADMINISTRAR sobre el modulo USUARIOS.
		 */
		if (!authorizationService.tienePermiso(userDetails, MODULO_USUARIOS, PERMISO_ADMINISTRAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para administrar usuarios.");
		}
	}
}
