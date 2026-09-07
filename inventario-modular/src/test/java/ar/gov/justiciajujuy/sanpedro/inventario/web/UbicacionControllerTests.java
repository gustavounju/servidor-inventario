package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
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
class UbicacionControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void creaListaYEditaUbicacion() throws Exception {
		String crear = """
				{
				  "codigo": "UBI-INF-001",
				  "nombre": "Deposito Informatica",
				  "tipo": "DEPOSITO",
				  "fuero": "Informatica",
				  "responsable": "admin.local",
				  "edificio": "Centro Judicial San Pedro",
				  "piso": "PB",
				  "estado": "ACTIVA",
				  "observaciones": "Stock tecnico",
				  "activo": true
				}
				""";
		String editar = """
				{
				  "codigo": "UBI-INF-001",
				  "nombre": "Deposito Informatica Norte",
				  "tipo": "DEPOSITO",
				  "fuero": "Informatica",
				  "responsable": "soporte",
				  "edificio": "Centro Judicial San Pedro",
				  "piso": "PB",
				  "estado": "ACTIVA",
				  "observaciones": "Stock y repuestos",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/ubicaciones")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(crear))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.codigo").value("UBI-INF-001"))
			.andExpect(jsonPath("$.tipo").value("DEPOSITO"));

		mockMvc.perform(get("/api/v1/ubicaciones?query=deposito&tipo=DEPOSITO&estado=ACTIVA").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.codigo == 'UBI-INF-001')]", hasSize(1)));

		mockMvc.perform(put("/api/v1/ubicaciones/2")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(editar))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.nombre").value("Deposito Informatica Norte"))
			.andExpect(jsonPath("$.responsable").value("soporte"));
	}

	@Test
	void muestraPantallaDeUbicaciones() throws Exception {
		mockMvc.perform(get("/admin/ubicaciones").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Ubicaciones registradas")))
			.andExpect(content().string(containsString("UBI-SEED-001")));
	}

	@Test
	void bloqueaUbicacionesSinPermiso() throws Exception {
		mockMvc.perform(get("/api/v1/ubicaciones").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden());
	}

	@Test
	void respondeConflictCuandoElCodigoDeUbicacionYaExiste() throws Exception {
		String duplicada = """
				{
				  "codigo": "UBI-SEED-001",
				  "nombre": "Oficina duplicada",
				  "tipo": "OFICINA",
				  "estado": "ACTIVA",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/ubicaciones")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(duplicada))
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
