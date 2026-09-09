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
import com.jayway.jsonpath.JsonPath;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.context.jdbc.SqlMergeMode;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Sql(scripts = "/sql/limpiar-seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@Sql(scripts = "/sql/seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@SqlMergeMode(SqlMergeMode.MergeMode.MERGE)
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
				  "solicitanteUsername": "mesa.entrada",
				  "solicitanteNombre": "Mesa de Entrada",
				  "solicitanteFuero": "Mesa de ayuda",
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
			.andExpect(jsonPath("$.solicitanteUsername").value("mesa.entrada"))
			.andExpect(jsonPath("$.solicitanteNombre").value("Mesa de Entrada"))
			.andExpect(jsonPath("$.equipoNombre").value("PC-INF-001"));

		mockMvc.perform(get("/api/v1/tareas-tecnicas?estado=PENDIENTE&equipoId=1").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.titulo == 'Revisar fuente de PC-INF-001')]", hasSize(1)));

		mockMvc.perform(get("/api/v1/tareas-tecnicas?responsable=apagados").with(user(adminLocal())))
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
				  "solicitanteUsername": "mesa.entrada",
				  "solicitanteNombre": "Mesa de Entrada",
				  "solicitanteFuero": "Mesa de ayuda",
				  "prioridad": "MEDIA",
				  "responsable": "mesa"
				}
				""";
		String actualizacion = """
				{
				  "equipoId": null,
				  "titulo": "Revisar equipo y perifericos",
				  "descripcion": "Se agrega control de teclado y monitor.",
				  "solicitanteUsername": "mesa.entrada",
				  "solicitanteNombre": "Mesa de Entrada",
				  "solicitanteFuero": "Mesa de ayuda",
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
			.andExpect(jsonPath("$.equipoNombre").value("PC-GENERICA"));
	}

	@Test
	@Sql(statements = {
			"INSERT INTO usuarios (id, username, nombre_visible, fuero, origen, activo) VALUES (3, 'tecnico.local', 'Tecnico Local', 'Informatica', 'AD', TRUE)",
			"INSERT INTO roles (id, codigo, nombre, descripcion, activo) VALUES (2, 'TECNICO', 'Tecnico', 'Acceso operativo a tareas tecnicas.', TRUE)",
			"INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (3, 2)",
			"INSERT INTO rol_modulo_permisos (rol_id, modulo_id, permiso_id) VALUES (2, 9, 1), (2, 9, 3)"
	})
	void tecnicoComunQuedaComoResponsableYPuedeTomarTareaLibre() throws Exception {
		String tareaPropia = """
				{
				  "equipoId": null,
				  "titulo": "Configurar acceso a impresora",
				  "descripcion": "Solicitud de mesa de entrada.",
				  "solicitanteUsername": "mesa.entrada",
				  "solicitanteNombre": "Mesa de Entrada",
				  "solicitanteFuero": "Mesa de ayuda",
				  "prioridad": "MEDIA",
				  "responsable": "otro.tecnico"
				}
				""";
		String tareaLibre = """
				{
				  "equipoId": null,
				  "titulo": "Tarea disponible para tomar",
				  "descripcion": "Alta creada por administrador.",
				  "solicitanteUsername": "mesa.entrada",
				  "solicitanteNombre": "Mesa de Entrada",
				  "solicitanteFuero": "Mesa de ayuda",
				  "prioridad": "BAJA",
				  "responsable": null
				}
				""";

		mockMvc.perform(post("/api/v1/tareas-tecnicas")
				.with(user(tecnicoLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(tareaPropia))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.responsable").value("tecnico.local"))
			.andExpect(jsonPath("$.equipoNombre").value("PC-GENERICA"));

		String creada = mockMvc.perform(post("/api/v1/tareas-tecnicas")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(tareaLibre))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.responsable").doesNotExist())
			.andReturn().getResponse().getContentAsString();
		Number tareaId = JsonPath.read(creada, "$.id");

		mockMvc.perform(post("/api/v1/tareas-tecnicas/{id}/tomar", tareaId)
				.with(user(tecnicoLocal()))
				.with(csrf()))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.responsable").value("tecnico.local"))
			.andExpect(jsonPath("$.estado").value("EN_PROCESO"));
	}

	@Test
	@Sql(statements = {
			"INSERT INTO usuarios (id, username, nombre_visible, fuero, origen, activo) VALUES (3, 'tecnico.local', 'Tecnico Local', 'Informatica', 'AD', TRUE)",
			"INSERT INTO roles (id, codigo, nombre, descripcion, activo) VALUES (2, 'TECNICO', 'Tecnico', 'Acceso operativo a tareas tecnicas.', TRUE)",
			"INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (3, 2)",
			"INSERT INTO rol_modulo_permisos (rol_id, modulo_id, permiso_id) VALUES (2, 9, 1), (2, 9, 3)"
	})
	void tecnicoNoOperaTareaDeOtroResponsable() throws Exception {
		String comentario = """
				{
				  "comentario": "Intento intervenir tarea ajena."
				}
				""";

		mockMvc.perform(post("/api/v1/tareas-tecnicas/1/comentarios")
				.with(user(tecnicoLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(comentario))
			.andExpect(status().isForbidden());
	}

	@Test
	void agregaYListaComentariosDeTareaTecnica() throws Exception {
		String comentario = """
				{
				  "comentario": "Se coordino visita con mesa de entradas."
				}
				""";

		mockMvc.perform(post("/api/v1/tareas-tecnicas/1/comentarios")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(comentario))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.tareaId").value(1))
			.andExpect(jsonPath("$.autor").value("admin.local"))
			.andExpect(jsonPath("$.comentario").value("Se coordino visita con mesa de entradas."));

		mockMvc.perform(get("/api/v1/tareas-tecnicas/1/comentarios").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.comentario == 'Se coordino visita con mesa de entradas.')]", hasSize(1)));
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

	private ActiveDirectoryUserDetails tecnicoLocal() {
		return new ActiveDirectoryUserDetails(
				"tecnico.local",
				"unused",
				List.of(new SimpleGrantedAuthority("ROLE_USER")),
				"Tecnico Local",
				"Informatica",
				Map.of("origen", List.of("AD_TEST")));
	}
}
