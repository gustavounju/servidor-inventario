package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.not;
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
import org.springframework.test.context.jdbc.SqlMergeMode;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Sql(scripts = "/sql/limpiar-seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@Sql(scripts = "/sql/seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@SqlMergeMode(SqlMergeMode.MergeMode.MERGE)
class EquipoGenericoPageControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	@Sql(statements = {
			"INSERT INTO equipos (id, nombre, ultimo_usuario, fuero, ubicacion, sistema_operativo, monitoreo, activo) VALUES (3, 'PC-GENERICA', 'Sin asignar', 'Sin fuero informado', 'Mesa de ayuda', 'No aplica', 'AUXILIAR_TAREAS', TRUE)",
			"INSERT INTO tareas_tecnicas (id, equipo_id, titulo, descripcion, solicitante_username, solicitante_nombre, solicitante_fuero, estado, prioridad, responsable, creado_por) VALUES (2, 3, 'Reclamo sin PC identificada', 'El usuario no conoce el nombre del equipo.', 'mesa.entrada', 'Mesa de Entrada', 'Mesa de ayuda', 'PENDIENTE', 'ALTA', 'admin.local', 'admin.local')",
			"INSERT INTO tareas_tecnicas_comentarios (id, tarea_id, autor, comentario) VALUES (2, 2, 'admin.local', 'Se pidio confirmar el puesto real.')"
	})
	void muestraSoloTareasEnPcGenerica() throws Exception {
		mockMvc.perform(get("/admin/equipos/3").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/equipo-detalle"))
			.andExpect(content().string(containsString("Tareas auxiliares")))
			.andExpect(content().string(containsString("Reclamo sin PC identificada")))
			.andExpect(content().string(containsString("Mesa de Entrada")))
			.andExpect(content().string(containsString("Mesa de ayuda")))
			.andExpect(content().string(containsString("admin.local")))
			.andExpect(content().string(containsString("Se pidio confirmar el puesto real.")))
			.andExpect(content().string(containsString("/admin/equipos/generico/tareas/2/reasignar")))
			.andExpect(content().string(not(containsString("Ver en tareas"))))
			.andExpect(content().string(not(containsString("Copiar Comando PowerShell"))))
			.andExpect(content().string(not(containsString("Carga Masiva de Piezas"))))
			.andExpect(content().string(not(containsString("Ficha Técnica y Hardware"))))
			.andExpect(content().string(not(containsString("Gemelo digital"))));
	}

	@Test
	void listadoDeEquiposPermiteAbrirTareasDelEquipo() throws Exception {
		mockMvc.perform(get("/admin/equipos").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/equipos"))
			.andExpect(content().string(containsString("Tareas")))
			.andExpect(content().string(containsString("/admin/tareas?equipoId=1")))
			.andExpect(content().string(containsString("/admin/tareas?equipoId=2")));
	}

	@Test
	@Sql(statements = {
			"INSERT INTO equipos (id, nombre, ultimo_usuario, fuero, ubicacion, sistema_operativo, monitoreo, activo) VALUES (3, 'PC-GENERICA', 'Sin asignar', 'Sin fuero informado', 'Mesa de ayuda', 'No aplica', 'AUXILIAR_TAREAS', TRUE)",
			"INSERT INTO tareas_tecnicas (id, equipo_id, titulo, descripcion, solicitante_username, solicitante_nombre, solicitante_fuero, estado, prioridad, responsable, creado_por) VALUES (2, 3, 'Reclamo sin PC identificada', 'El usuario no conoce el nombre del equipo.', 'mesa.entrada', 'Mesa de Entrada', 'Mesa de ayuda', 'PENDIENTE', 'ALTA', 'admin.local', 'admin.local')"
	})
	void administradorReasignaTareaGenericaAEquipoReal() throws Exception {
		mockMvc.perform(post("/admin/equipos/generico/tareas/2/reasignar")
				.with(user(adminLocal()))
				.with(csrf())
				.param("equipoDestinoId", "1"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/equipos/3?actualizado=*"));

		mockMvc.perform(get("/admin/tareas?equipoId=1").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Reclamo sin PC identificada")))
			.andExpect(content().string(containsString("PC-INF-001")));

		mockMvc.perform(get("/admin/equipos/3").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(not(containsString("Reclamo sin PC identificada"))));
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
}
