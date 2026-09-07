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
class PatrimonioPageControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void muestraPantallaYCargaBienPatrimonial() throws Exception {
		mockMvc.perform(get("/admin/patrimonio").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/patrimonio"))
			.andExpect(content().string(containsString("Patrimonio")))
			.andExpect(content().string(containsString("Cargar bien patrimonial")));

		mockMvc.perform(post("/admin/patrimonio/bienes")
				.with(user(adminLocal()))
				.with(csrf())
				.param("numeroPatrimonial", "PAT-PAGE-001")
				.param("categoria", "PC")
				.param("descripcion", "PC administrativa con etiqueta patrimonial")
				.param("ubicacion", "Informatica")
				.param("fuero", "Informatica")
				.param("custodio", "gmurad")
				.param("estado", "EN_USO")
				.param("equipoId", "1")
				.param("activo", "true"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/patrimonio?creado=*"));

		mockMvc.perform(get("/admin/patrimonio?query=PAT-PAGE").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("PAT-PAGE-001")))
			.andExpect(content().string(containsString("PC administrativa con etiqueta patrimonial")))
			.andExpect(content().string(containsString("PC-INF-001")));
	}

	@Test
	void bloqueaPantallaSinPermiso() throws Exception {
		mockMvc.perform(get("/admin/patrimonio").with(user(usuarioSinPermisos())))
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
