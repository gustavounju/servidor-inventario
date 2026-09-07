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
class PatrimonioControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void creaListaYEditaBienPatrimonial() throws Exception {
		String crear = """
				{
				  "numeroPatrimonial": "PJ-2026-0001",
				  "categoria": "PC",
				  "descripcion": "PC administrativa inventariada",
				  "ubicacion": "Informatica",
				  "fuero": "Informatica",
				  "custodio": "gmurad",
				  "estado": "EN_USO",
				  "equipoId": 1,
				  "observaciones": "Alta inicial",
				  "activo": true
				}
				""";
		String editar = """
				{
				  "numeroPatrimonial": "PJ-2026-0001",
				  "categoria": "PC",
				  "descripcion": "PC administrativa reasignada",
				  "ubicacion": "Mesa de ayuda",
				  "fuero": "Informatica",
				  "custodio": "soporte",
				  "estado": "EN_USO",
				  "equipoId": 1,
				  "observaciones": "Reasignada",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/patrimonio/bienes")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(crear))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.numeroPatrimonial").value("PJ-2026-0001"))
			.andExpect(jsonPath("$.equipoNombre").value("PC-INF-001"));

		mockMvc.perform(get("/api/v1/patrimonio/bienes?query=administrativa&estado=EN_USO").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.numeroPatrimonial == 'PJ-2026-0001')]", hasSize(1)));

		mockMvc.perform(put("/api/v1/patrimonio/bienes/2")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(editar))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.descripcion").value("PC administrativa reasignada"))
			.andExpect(jsonPath("$.custodio").value("soporte"));
	}

	@Test
	void bloqueaPatrimonioSinPermiso() throws Exception {
		mockMvc.perform(get("/api/v1/patrimonio/bienes").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden());
	}

	@Test
	void respondeConflictCuandoElNumeroPatrimonialYaExiste() throws Exception {
		String duplicado = """
				{
				  "numeroPatrimonial": "PAT-SEED-001",
				  "categoria": "PC",
				  "descripcion": "Bien duplicado",
				  "estado": "EN_USO",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/patrimonio/bienes")
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
