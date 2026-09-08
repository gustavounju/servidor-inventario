package ar.gov.justiciajujuy.sanpedro.inventario.security;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestBuilders.formLogin;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.view;

import java.util.List;
import java.util.Map;
import java.util.Set;

import ar.gov.justiciajujuy.sanpedro.inventario.config.SiteAvailabilityService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.CrearUsuarioCommand;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;

@SpringBootTest(properties = {
		"inventario.local-auth.enabled=true",
		"inventario.local-auth.username=admin.local",
		"inventario.local-auth.password=AdminLocal123",
		"inventario.local-db-auth.enabled=true"
})
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Sql(scripts = "/sql/limpiar-seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@Sql(scripts = "/sql/seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
class SiteMaintenanceModeTests {

	@Autowired
	private MockMvc mockMvc;

	@Autowired
	private SiteAvailabilityService siteAvailabilityService;

	@Autowired
	private UsuarioManagementService usuarioManagementService;

	@Test
	void loginMuestraEstadoInactivoCuandoMantenimientoEstaActivo() throws Exception {
		siteAvailabilityService.update(true, "Actualizacion programada", "gmurad");

		mockMvc.perform(get("/login"))
			.andExpect(status().isOk())
			.andExpect(view().name("login"))
			.andExpect(content().string(containsString("Sitio temporalmente inactivo")))
			.andExpect(content().string(containsString("Actualizacion programada")))
			.andExpect(content().string(containsString("gmurad")));
	}

	@Test
	void mantenimientoBloqueaLoginDeUsuariosNoAutorizados() throws Exception {
		crearUsuarioLocal("tecnico.local", "Tecnico Local", "TecnicoLocal123");
		siteAvailabilityService.update(true, "Actualizacion programada", "gmurad");

		mockMvc.perform(formLogin()
				.user("tecnico.local")
				.password("TecnicoLocal123"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/login?inactive"));
	}

	@Test
	void mantenimientoPermiteLoginDelUsuarioDeEmergencia() throws Exception {
		crearUsuarioLocal("gmurad", "Gustavo Murad", "GmuradLocal123");
		siteAvailabilityService.update(true, "Actualizacion programada", "gmurad");

		mockMvc.perform(formLogin()
				.user("gmurad")
				.password("GmuradLocal123"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin"));
	}

	@Test
	void administradorPuedeCambiarEstadoDelSitio() throws Exception {
		crearUsuarioLocal("gmurad", "Gustavo Murad", "GmuradLocal123");

		mockMvc.perform(post("/admin/sitio")
				.with(user(adminLocal()))
				.with(csrf())
				.param("temporarilyInactive", "true")
				.param("message", "Ventana de mantenimiento")
				.param("allowedUsername", "gmurad"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin/sitio?updated=true"));

		mockMvc.perform(get("/admin/sitio").with(user(gmurad())))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/sitio"))
			.andExpect(content().string(containsString("Estado del sitio")))
			.andExpect(content().string(containsString("Ventana de mantenimiento")))
			.andExpect(content().string(containsString("gmurad")));
	}

	@Test
	void usuarioSinPermisoNoPuedeCambiarEstadoDelSitio() throws Exception {
		mockMvc.perform(post("/admin/sitio")
				.with(user(usuarioSinPermisos()))
				.with(csrf())
				.param("temporarilyInactive", "true")
				.param("message", "Ventana de mantenimiento")
				.param("allowedUsername", "gmurad"))
			.andExpect(status().isForbidden());
	}

	private void crearUsuarioLocal(String username, String nombreVisible, String password) {
		usuarioManagementService.crearUsuario(new CrearUsuarioCommand(
				username,
				nombreVisible,
				"Informatica",
				"LOCAL",
				password,
				true,
				Set.of("ADMINISTRADOR")));
	}

	private ActiveDirectoryUserDetails adminLocal() {
		return new ActiveDirectoryUserDetails(
				"admin.local",
				"unused",
				List.of(new SimpleGrantedAuthority("ROLE_USER")),
				"Administrador Local",
				"Desarrollo local",
				Map.of("origen", List.of("LOCAL_SIMULADO")));
	}

	private ActiveDirectoryUserDetails gmurad() {
		return new ActiveDirectoryUserDetails(
				"gmurad",
				"unused",
				List.of(new SimpleGrantedAuthority("ROLE_USER")),
				"Gustavo Murad",
				"Informatica",
				Map.of("origen", List.of("LOCAL_TEST")));
	}

	private ActiveDirectoryUserDetails usuarioSinPermisos() {
		return new ActiveDirectoryUserDetails(
				"sin.permisos",
				"unused",
				List.of(new SimpleGrantedAuthority("ROLE_USER")),
				"Usuario Sin Permisos",
				"Mesa de ayuda",
				Map.of("origen", List.of("AD_TEST")));
	}
}
