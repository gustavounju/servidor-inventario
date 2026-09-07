package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrlPattern;
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
class MueblePageControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void muestraPantallaYCargaMueble() throws Exception {
		mockMvc.perform(get("/admin/muebles").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/muebles"))
			.andExpect(content().string(containsString("Muebles")))
			.andExpect(content().string(containsString("Cargar mueble")));

		mockMvc.perform(post("/admin/muebles")
				.with(user(adminLocal()))
				.with(csrf())
				.param("codigo", "MUE-PAGE-001")
				.param("tipo", "ESCRITORIO")
				.param("descripcion", "Escritorio para mesa de ayuda")
				.param("ubicacion", "Mesa de ayuda")
				.param("fuero", "Informatica")
				.param("responsable", "soporte")
				.param("estado", "ACTIVO")
				.param("activo", "true"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/muebles?creado=*"));

		mockMvc.perform(get("/admin/muebles?query=MUE-PAGE").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("MUE-PAGE-001")))
			.andExpect(content().string(containsString("Escritorio para mesa de ayuda")));
	}

	@Test
	void bloqueaPantallaSinPermiso() throws Exception {
		mockMvc.perform(get("/admin/muebles").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden());
	}

	private ActiveDirectoryUserDetails adminLocal() {
		return new ActiveDirectoryUserDetails("admin.local", "unused", List.of(new SimpleGrantedAuthority("ROLE_USER")),
				"Administrador Local", "Desarrollo local", Map.of("origen", List.of("LOCAL_SIMULADO")));
	}

	private ActiveDirectoryUserDetails usuarioSinPermisos() {
		return new ActiveDirectoryUserDetails("sin.permisos", "unused", List.of(new SimpleGrantedAuthority("ROLE_USER")),
				"Usuario Sin Permisos", "Mesa de ayuda", Map.of("origen", List.of("AD_TEST")));
	}
}
