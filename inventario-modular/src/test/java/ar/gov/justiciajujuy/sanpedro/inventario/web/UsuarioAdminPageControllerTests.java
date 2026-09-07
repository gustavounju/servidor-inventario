package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.containsString;
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

import ar.gov.justiciajujuy.sanpedro.inventario.security.ActiveDirectoryUserDetails;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Sql(scripts = "/sql/limpiar-seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@Sql(scripts = "/sql/seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
class UsuarioAdminPageControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void muestraPantallaDeAdministracionParaUsuariosAutorizados() throws Exception {
		mockMvc.perform(get("/admin/usuarios").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/usuarios"))
			.andExpect(content().string(containsString("Administracion de usuarios")))
			.andExpect(content().string(containsString("Crear usuario local")))
			.andExpect(content().string(containsString("Usuarios de dominio")))
			.andExpect(content().string(containsString("Buscar AD")))
			.andExpect(content().string(containsString("Buscar usuario AD")))
			.andExpect(content().string(containsString("Ingrese al menos 2 caracteres para buscar usuarios de dominio.")))
			.andExpect(content().string(containsString("admin.local")))
			.andExpect(content().string(containsString("ADMINISTRADOR")));
	}

	@Test
	void muestraEstadoLdapAlBuscarUsuariosDeDominio() throws Exception {
		mockMvc.perform(get("/admin/usuarios")
				.param("q", "gmurad")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("No disponible")))
			.andExpect(content().string(containsString("LDAP esta desactivado en este entorno.")));
	}

	@Test
	void bloqueaPantallaDeAdministracionSiNoTienePermiso() throws Exception {
		mockMvc.perform(get("/admin/usuarios").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden());
	}

	@Test
	void creaUsuarioDesdeFormularioWeb() throws Exception {
		mockMvc.perform(post("/admin/usuarios")
				.with(user(adminLocal()))
				.with(csrf())
				.param("username", "tecnico.local")
				.param("nombreVisible", "Tecnico Local")
				.param("fuero", "Informatica")
				.param("password", "TecnicoLocal123")
				.param("activo", "true")
				.param("roles", "ADMINISTRADOR"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin/usuarios?creado=tecnico.local"));

		mockMvc.perform(get("/admin/usuarios").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("tecnico.local")))
			.andExpect(content().string(containsString("Tecnico Local")));
	}

	@Test
	void autorizaUsuarioDominioDesdeFormularioWebSinClaveLocal() throws Exception {
		mockMvc.perform(post("/admin/usuarios/dominio")
				.with(user(adminLocal()))
				.with(csrf())
				.param("username", "gmurad")
				.param("nombreVisible", "Gustavo Elias Murad")
				.param("fuero", "Informatica")
				.param("activo", "true")
				.param("roles", "ADMINISTRADOR"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin/usuarios?q=gmurad&autorizado=gmurad"));

		mockMvc.perform(get("/admin/usuarios").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("gmurad")))
			.andExpect(content().string(containsString("Gustavo Elias Murad")))
			.andExpect(content().string(containsString("AD")));
	}

	@Test
	void editaUsuarioDesdeFormularioWeb() throws Exception {
		mockMvc.perform(post("/admin/usuarios/editar")
				.with(user(adminLocal()))
				.with(csrf())
				.param("id", "2")
				.param("activo", "true")
				.param("roles", "ADMINISTRADOR"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin/usuarios?actualizado=true"));

		mockMvc.perform(get("/admin/usuarios?actualizado=true").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Usuario actualizado correctamente.")));
	}

	@Test
	void cambiaClaveLocalDesdeFormularioWeb() throws Exception {
		mockMvc.perform(post("/admin/usuarios/cambiar-clave")
				.with(user(adminLocal()))
				.with(csrf())
				.param("id", "1")
				.param("password", "NuevaClaveSuperSegura123!"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin/usuarios?claveCambiada=true"));

		mockMvc.perform(get("/admin/usuarios?claveCambiada=true").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Clave del usuario modificada correctamente.")));
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
