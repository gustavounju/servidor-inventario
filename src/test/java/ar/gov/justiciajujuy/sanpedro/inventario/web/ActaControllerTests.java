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
class ActaControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void creaListaYEditaActa() throws Exception {
		String crear = """
				{
				  "numero": "ACT-2026-001",
				  "tipo": "ENTREGA",
				  "equipoId": 1,
				  "fechaEmision": "2026-09-01",
				  "destinatario": "Mesa de Entradas",
				  "responsableEntrega": "admin.local",
				  "responsableRecepcion": "mesa.entrada",
				  "detalle": "Entrega de PC con perifericos.",
				  "estado": "BORRADOR",
				  "observaciones": "Pendiente de firma",
				  "activo": true
				}
				""";
		String editar = """
				{
				  "numero": "ACT-2026-001",
				  "tipo": "ENTREGA",
				  "equipoId": 1,
				  "fechaEmision": "2026-09-01",
				  "destinatario": "Mesa de Entradas",
				  "responsableEntrega": "admin.local",
				  "responsableRecepcion": "mesa.entrada",
				  "detalle": "Entrega de PC confirmada.",
				  "estado": "EMITIDA",
				  "observaciones": "Firmada",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/actas")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(crear))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.numero").value("ACT-2026-001"))
			.andExpect(jsonPath("$.equipoNombre").value("PC-INF-001"));

		mockMvc.perform(get("/api/v1/actas?query=mesa&tipo=ENTREGA&estado=BORRADOR").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.numero == 'ACT-2026-001')]", hasSize(1)));

		mockMvc.perform(put("/api/v1/actas/2")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(editar))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.detalle").value("Entrega de PC confirmada."))
			.andExpect(jsonPath("$.estado").value("EMITIDA"));
	}

	@Test
	void muestraPantallaDeActas() throws Exception {
		mockMvc.perform(get("/admin/actas").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Actas registradas")))
			.andExpect(content().string(containsString("ACT-SEED-001")));
	}

	@Test
	void bloqueaActasSinPermiso() throws Exception {
		mockMvc.perform(get("/api/v1/actas").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden());
	}

	@Test
	void respondeConflictCuandoElNumeroDeActaYaExiste() throws Exception {
		String duplicada = """
				{
				  "numero": "ACT-SEED-001",
				  "tipo": "ENTREGA",
				  "fechaEmision": "2026-09-01",
				  "destinatario": "Mesa de Entradas",
				  "detalle": "Acta duplicada.",
				  "estado": "BORRADOR",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/actas")
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
