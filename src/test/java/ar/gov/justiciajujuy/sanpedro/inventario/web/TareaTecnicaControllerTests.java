package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
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
class TareaTecnicaControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void creaListaYCierraTareaTecnica() throws Exception {
		String tarea = """
				{
				  "equipoId": 1,
				  "titulo": "Revisar fuente de PC-INF-001",
				  "descripcion": "Equipo reporta apagados intermitentes.",
				  "prioridad": "ALTA",
				  "responsable": "gmurad"
				}
				""";
		String cierre = """
				{
				  "estado": "CERRADA",
				  "observacionesCierre": "Se cambio la fuente y se verifico encendido."
				}
				""";

		mockMvc.perform(post("/api/v1/tareas-tecnicas")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(tarea))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.titulo").value("Revisar fuente de PC-INF-001"))
			.andExpect(jsonPath("$.estado").value("PENDIENTE"))
			.andExpect(jsonPath("$.prioridad").value("ALTA"))
			.andExpect(jsonPath("$.equipoNombre").value("PC-INF-001"));

		mockMvc.perform(get("/api/v1/tareas-tecnicas?estado=PENDIENTE&equipoId=1").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.titulo == 'Revisar fuente de PC-INF-001')]", hasSize(1)));

		mockMvc.perform(patch("/api/v1/tareas-tecnicas/1/estado")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(cierre))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.estado").value("CERRADA"))
			.andExpect(jsonPath("$.observacionesCierre").value("Se cambio la fuente y se verifico encendido."));
	}

	@Test
	void actualizaDatosDeTareaTecnica() throws Exception {
		String tarea = """
				{
				  "equipoId": 1,
				  "titulo": "Revisar equipo",
				  "descripcion": "Pendiente de diagnostico.",
				  "prioridad": "MEDIA",
				  "responsable": "mesa"
				}
				""";
		String actualizacion = """
				{
				  "equipoId": null,
				  "titulo": "Revisar equipo y perifericos",
				  "descripcion": "Se agrega control de teclado y monitor.",
				  "prioridad": "ALTA",
				  "responsable": "gmurad"
				}
				""";

		mockMvc.perform(post("/api/v1/tareas-tecnicas")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(tarea))
			.andExpect(status().isCreated());

		mockMvc.perform(put("/api/v1/tareas-tecnicas/1")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(actualizacion))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.titulo").value("Revisar equipo y perifericos"))
			.andExpect(jsonPath("$.descripcion").value("Se agrega control de teclado y monitor."))
			.andExpect(jsonPath("$.prioridad").value("ALTA"))
			.andExpect(jsonPath("$.responsable").value("gmurad"))
			.andExpect(jsonPath("$.equipoId").doesNotExist());
	}

	@Test
	void bloqueaTareasSinPermiso() throws Exception {
		mockMvc.perform(get("/api/v1/tareas-tecnicas").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden());
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
