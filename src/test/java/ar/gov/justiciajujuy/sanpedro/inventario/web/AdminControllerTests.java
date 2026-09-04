package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.not;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

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
class AdminControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void muestraAccesoUsuariosSiPuedeAdministrarUsuarios() throws Exception {
		mockMvc.perform(get("/admin").with(user(usuario("admin.local"))))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("href=\"/admin/usuarios\"")))
			.andExpect(content().string(containsString("Brújula Operativa")))
			.andExpect(content().string(not(containsString("Modo de trabajo"))));
	}

	@Test
	void muestraAccesoEquiposSiPuedeVerEquipos() throws Exception {
		mockMvc.perform(get("/admin").with(user(usuario("admin.local"))))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("href=\"/admin/equipos\"")))
			.andExpect(content().string(containsString("href=\"/admin/dashboard-diferencias\"")))
			.andExpect(content().string(containsString("href=\"/admin/stock\"")))
			.andExpect(content().string(containsString("href=\"/admin/ordenes-armado\"")))
			.andExpect(content().string(containsString("href=\"/admin/actas\"")))
			.andExpect(content().string(containsString("href=\"/admin/ubicaciones\"")))
			.andExpect(content().string(containsString("href=\"/admin/auditoria\"")));
	}

	@Test
	void ocultaAccesoUsuariosSiNoPuedeAdministrarUsuarios() throws Exception {
		mockMvc.perform(get("/admin").with(user(usuario("sin.permisos"))))
			.andExpect(status().isOk())
			.andExpect(content().string(not(containsString("href=\"/admin/usuarios\""))));
	}

	@Test
	void ocultaAccesoEquiposSiNoPuedeVerEquipos() throws Exception {
		mockMvc.perform(get("/admin").with(user(usuario("sin.permisos"))))
			.andExpect(status().isOk())
			.andExpect(content().string(not(containsString("href=\"/admin/equipos\""))))
			.andExpect(content().string(not(containsString("href=\"/admin/dashboard-diferencias\""))))
			.andExpect(content().string(not(containsString("href=\"/admin/stock\""))))
			.andExpect(content().string(not(containsString("href=\"/admin/ordenes-armado\""))))
			.andExpect(content().string(not(containsString("href=\"/admin/actas\""))))
			.andExpect(content().string(not(containsString("href=\"/admin/ubicaciones\""))))
			.andExpect(content().string(not(containsString("href=\"/admin/auditoria\""))));
	}

	private ActiveDirectoryUserDetails usuario(String username) {
		return new ActiveDirectoryUserDetails(
				username,
				"unused",
				List.of(new SimpleGrantedAuthority("ROLE_USER")),
				username,
				"Informatica",
				Map.of());
	}
}
