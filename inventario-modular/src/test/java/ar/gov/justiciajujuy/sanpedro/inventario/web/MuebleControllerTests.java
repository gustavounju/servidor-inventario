package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;
import java.util.Map;

import ar.gov.justiciajujuy.sanpedro.inventario.security.ActiveDirectoryUserDetails;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Sql(scripts = "/sql/limpiar-seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@Sql(scripts = "/sql/seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
class MuebleControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void creaListaYEditaMueble() throws Exception {
		String crear = """
				{
				  "codigo": "MUE-001",
				  "tipo": "ESCRITORIO",
				  "descripcion": "Escritorio de mesa de entradas",
				  "ubicacion": "Mesa de Entradas",
				  "fuero": "Civil",
				  "responsable": "mesa.entrada",
				  "estado": "ACTIVO",
				  "observaciones": "Alta inicial",
				  "activo": true
				}
				""";
		String editar = """
				{
				  "codigo": "MUE-001",
				  "tipo": "ESCRITORIO",
				  "descripcion": "Escritorio reasignado",
				  "ubicacion": "Secretaria",
				  "fuero": "Civil",
				  "responsable": "secretaria",
				  "estado": "EN_REPARACION",
				  "observaciones": "Revisar cajonera",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/muebles")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(crear))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.codigo").value("MUE-001"))
			.andExpect(jsonPath("$.estado").value("ACTIVO"));

		mockMvc.perform(get("/api/v1/muebles?query=mesa&estado=ACTIVO").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.codigo == 'MUE-001')]", hasSize(1)));

		mockMvc.perform(put("/api/v1/muebles/2")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(editar))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.descripcion").value("Escritorio reasignado"))
			.andExpect(jsonPath("$.estado").value("EN_REPARACION"));
	}

	@Test
	void bloqueaMueblesSinPermiso() throws Exception {
		mockMvc.perform(get("/api/v1/muebles").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden());
	}

	@Test
	void respondeConflictCuandoElCodigoDeMuebleYaExiste() throws Exception {
		String duplicado = """
				{
				  "codigo": "MUE-SEED-001",
				  "tipo": "SILLA",
				  "descripcion": "Silla duplicada",
				  "estado": "ACTIVO",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/muebles")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(duplicado))
			.andExpect(status().isConflict());
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
