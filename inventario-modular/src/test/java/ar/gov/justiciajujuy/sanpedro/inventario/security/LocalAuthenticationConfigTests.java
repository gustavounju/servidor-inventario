package ar.gov.justiciajujuy.sanpedro.inventario.security;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestBuilders.formLogin;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@SpringBootTest(properties = {
		"inventario.local-auth.enabled=true",
		"inventario.local-auth.username=admin.local",
		"inventario.local-auth.password=ClaveLocal123!",
		"inventario.local-auth.display-name=Administrador Local de Prueba",
		"inventario.local-auth.fuero=Desarrollo local",
		"inventario.ldap.enabled=false"
})
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Sql(scripts = "/sql/limpiar-seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@Sql(scripts = "/sql/seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
class LocalAuthenticationConfigTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void allowsLocalLoginWhenLdapIsDisabled() throws Exception {
		/*
		 * Simula el escenario de casa: no hay dominio disponible, pero el perfil local
		 * permite ingresar con un usuario controlado por configuracion.
		 */
		MvcResult login = mockMvc.perform(formLogin()
				.user("admin.local")
				.password("ClaveLocal123!"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin"))
			.andReturn();

		mockMvc.perform(get("/admin").session((org.springframework.mock.web.MockHttpSession) login.getRequest().getSession(false)))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Administrador Local")))
			.andExpect(content().string(containsString("Equipos")))
			.andExpect(content().string(containsString("Usuarios")));
	}

	@Test
	void rejectsLocalLoginWithWrongPassword() throws Exception {
		mockMvc.perform(formLogin()
				.user("admin.local")
				.password("clave-equivocada"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/login?error"));
	}

	@Test
	void allowsRepeatedLocalLoginsWithSameCredentials() throws Exception {
		/*
		 * Spring Security borra las credenciales del UserDetails autenticado despues
		 * de cada login. El proveedor local debe devolver una instancia nueva para que
		 * un primer ingreso correcto no rompa los intentos siguientes.
		 */
		mockMvc.perform(formLogin()
				.user("admin.local")
				.password("ClaveLocal123!"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin"));

		mockMvc.perform(formLogin()
				.user("admin.local")
				.password("ClaveLocal123!"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin"));
	}
}
