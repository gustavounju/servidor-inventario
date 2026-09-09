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
import org.springframework.test.context.jdbc.SqlMergeMode;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Sql(scripts = "/sql/limpiar-seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@Sql(scripts = "/sql/seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@SqlMergeMode(SqlMergeMode.MergeMode.MERGE)
class TareaTecnicaPageControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void muestraPantallaYCargaTareaTecnica() throws Exception {
		mockMvc.perform(get("/admin/tareas").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/tareas"))
			.andExpect(content().string(containsString("Tareas tecnicas")))
			.andExpect(content().string(containsString("Texto")))
			.andExpect(content().string(containsString("Comentario inicial de seguimiento.")))
			.andExpect(content().string(containsString("Nueva tarea")))
			.andExpect(content().string(containsString("Fuero / Unidad organizativa")))
			.andExpect(content().string(containsString("id=\"solicitante-fuero\"")))
			.andExpect(content().string(containsString("Mesa de ayuda")));

		mockMvc.perform(post("/admin/tareas")
				.with(user(adminLocal()))
				.with(csrf())
				.param("equipoId", "1")
				.param("titulo", "Revisar impresora compartida")
				.param("descripcion", "No imprime desde mesa de entrada")
				.param("solicitanteUsername", "mesa.entrada")
				.param("solicitanteNombre", "Mesa de Entrada")
				.param("solicitanteFuero", "Mesa de ayuda")
				.param("prioridad", "MEDIA")
				.param("responsable", "gmurad"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/tareas?creado=*"));

		mockMvc.perform(get("/admin/tareas").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Revisar impresora compartida")))
			.andExpect(content().string(containsString("PC-INF-001")));
	}

	@Test
	void cambiaEstadoDesdePantalla() throws Exception {
		mockMvc.perform(post("/admin/tareas")
				.with(user(adminLocal()))
				.with(csrf())
				.param("equipoId", "1")
				.param("titulo", "Actualizar antivirus")
				.param("solicitanteUsername", "mesa.entrada")
				.param("solicitanteNombre", "Mesa de Entrada")
				.param("solicitanteFuero", "Mesa de ayuda")
				.param("prioridad", "ALTA")
				.param("responsable", "gmurad"))
			.andExpect(status().is3xxRedirection());

		mockMvc.perform(post("/admin/tareas/1/estado")
				.with(user(adminLocal()))
				.with(csrf())
				.param("estado", "CERRADA")
				.param("observacionesCierre", "Actualizacion verificada"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/tareas?creado=*"));

		mockMvc.perform(get("/admin/tareas?estado=CERRADA").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("CERRADA")))
			.andExpect(content().string(containsString("Actualizacion verificada")));
	}

	@Test
	void editaTareaDesdePantalla() throws Exception {
		mockMvc.perform(post("/admin/tareas")
				.with(user(adminLocal()))
				.with(csrf())
				.param("equipoId", "1")
				.param("titulo", "Revisar cableado")
				.param("descripcion", "Control inicial")
				.param("solicitanteUsername", "mesa.entrada")
				.param("solicitanteNombre", "Mesa de Entrada")
				.param("solicitanteFuero", "Mesa de ayuda")
				.param("prioridad", "MEDIA")
				.param("responsable", "mesa"))
			.andExpect(status().is3xxRedirection());

		mockMvc.perform(post("/admin/tareas/1")
				.with(user(adminLocal()))
				.with(csrf())
				.param("titulo", "Revisar cableado de red")
				.param("descripcion", "Se agenda visita tecnica")
				.param("solicitanteUsername", "mesa.entrada")
				.param("solicitanteNombre", "Mesa de Entrada")
				.param("solicitanteFuero", "Mesa de ayuda")
				.param("prioridad", "ALTA")
				.param("responsable", "gmurad"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/tareas?creado=*"));

		mockMvc.perform(get("/admin/tareas").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Revisar cableado de red")))
			.andExpect(content().string(containsString("Se agenda visita tecnica")))
			.andExpect(content().string(containsString("gmurad")));
	}

	@Test
	void agregaComentarioDesdePantalla() throws Exception {
		mockMvc.perform(post("/admin/tareas/1/comentarios")
				.with(user(adminLocal()))
				.with(csrf())
				.param("comentario", "Se agenda visita con el responsable."))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/tareas?creado=*"));

		mockMvc.perform(get("/admin/tareas").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Se agenda visita con el responsable.")));
	}

	@Test
	@Sql(statements = "INSERT INTO equipos (id, nombre, ultimo_usuario, fuero, ubicacion, sistema_operativo, monitoreo, activo) VALUES (3, 'PC-GENERICA', 'Sin asignar', 'Sin fuero informado', 'Mesa de ayuda', 'No aplica', 'AUXILIAR_TAREAS', TRUE)")
	void muestraAccesoATareasDePcGenericaSinOfrecerlaComoEquipoNormal() throws Exception {
		mockMvc.perform(get("/admin/tareas").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Tareas de PC genérica")))
			.andExpect(content().string(containsString("No se conoce el equipo")));
	}

	@Test
	void bloqueaPantallaSinPermiso() throws Exception {
		mockMvc.perform(get("/admin/tareas").with(user(usuarioSinPermisos())))
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
