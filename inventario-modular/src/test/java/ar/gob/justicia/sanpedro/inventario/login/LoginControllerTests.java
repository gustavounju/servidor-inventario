package ar.gob.justicia.sanpedro.inventario.login;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(properties = {
		"inventario.auth.local-admin.username=administrador",
		"inventario.auth.local-admin.password=admin-test-password"
})
@AutoConfigureMockMvc
class LoginControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void redirectsRootToLogin() throws Exception {
		mockMvc.perform(get("/"))
				.andExpect(status().is3xxRedirection())
				.andExpect(redirectedUrl("/login"));
	}

	@Test
	void rendersLoginShell() throws Exception {
		mockMvc.perform(get("/login"))
				.andExpect(status().isOk())
				.andExpect(content().contentTypeCompatibleWith(MediaType.TEXT_HTML))
				.andExpect(content().string(containsString("Inventario Modular")))
				.andExpect(content().string(containsString("Usuario")))
				.andExpect(content().string(containsString("Contrasena")))
				.andExpect(content().string(containsString("name=\"authMode\" value=\"local\" checked")))
				.andExpect(content().string(containsString("name=\"authMode\" value=\"domain\"")))
				.andExpect(content().string(org.hamcrest.Matchers.not(containsString("disabled"))));
	}

	@Test
	void authenticatesConfiguredLocalAdmin() throws Exception {
		mockMvc.perform(post("/login")
						.contentType(MediaType.APPLICATION_FORM_URLENCODED)
						.param("authMode", "local")
						.param("username", "administrador")
						.param("password", "admin-test-password"))
				.andExpect(status().isOk())
				.andExpect(content().string(containsString("/app")));
	}

	@Test
	void rejectsInvalidLocalCredentials() throws Exception {
		mockMvc.perform(post("/login")
						.contentType(MediaType.APPLICATION_FORM_URLENCODED)
						.param("authMode", "local")
						.param("username", "administrador")
						.param("password", "wrong"))
				.andExpect(status().isOk())
				.andExpect(content().string(containsString("Usuario o clave incorrectos.")));
	}

	@Test
	void explainsDomainModeIsPending() throws Exception {
		mockMvc.perform(post("/login")
						.contentType(MediaType.APPLICATION_FORM_URLENCODED)
						.param("authMode", "domain")
						.param("username", "gmurad")
						.param("password", "anything"))
				.andExpect(status().isOk())
				.andExpect(content().string(containsString("AD disponible")));
	}
}
