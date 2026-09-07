package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
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
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Sql(scripts = "/sql/limpiar-seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@Sql(scripts = "/sql/seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
class ReporteControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void exponeResumenYCsvOperativo() throws Exception {
		mockMvc.perform(get("/api/v1/reportes/resumen").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.equipos").value(2))
			.andExpect(jsonPath("$.muebles").value(1))
			.andExpect(jsonPath("$.bienesPatrimoniales").value(1))
			.andExpect(jsonPath("$.tareas").value(1))
			.andExpect(jsonPath("$.actas").value(1))
			.andExpect(jsonPath("$.ubicaciones").value(1));

		mockMvc.perform(get("/api/v1/reportes/muebles.csv").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("codigo,tipo,descripcion,ubicacion,fuero,responsable,estado,activo")))
			.andExpect(content().string(containsString("MUE-SEED-001")));

		mockMvc.perform(get("/api/v1/reportes/patrimonio.csv").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("numeroPatrimonial,categoria,descripcion,ubicacion,fuero,custodio,estado,equipoNombre,activo")))
			.andExpect(content().string(containsString("PAT-SEED-001")));

		mockMvc.perform(get("/api/v1/reportes/actas.csv").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("numero,tipo,equipoNombre,fechaEmision,destinatario,responsableEntrega,responsableRecepcion,estado,activo")))
			.andExpect(content().string(containsString("ACT-SEED-001")));

		mockMvc.perform(get("/api/v1/reportes/ubicaciones.csv").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("codigo,nombre,tipo,fuero,responsable,edificio,piso,estado,activo")))
			.andExpect(content().string(containsString("UBI-SEED-001")));
	}

	@Test
	void exportaCsvOperativoConFiltroTransversal() throws Exception {
		mockMvc.perform(get("/api/v1/reportes/muebles.csv")
				.param("query", "Informatica")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("MUE-SEED-001")));

		mockMvc.perform(get("/api/v1/reportes/muebles.csv")
				.param("query", "Sin coincidencia")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("codigo,tipo,descripcion,ubicacion,fuero,responsable,estado,activo")))
			.andExpect(content().string(org.hamcrest.Matchers.not(containsString("MUE-SEED-001"))));

		mockMvc.perform(get("/api/v1/reportes/patrimonio.csv")
				.param("query", "admin.local")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("PAT-SEED-001")));

		mockMvc.perform(get("/api/v1/reportes/actas.csv")
				.param("query", "Mesa")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("ACT-SEED-001")));

		mockMvc.perform(get("/api/v1/reportes/ubicaciones.csv")
				.param("query", "Centro Judicial")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("UBI-SEED-001")));
	}

	@Test
	void bloqueaReportesSinPermiso() throws Exception {
		mockMvc.perform(get("/api/v1/reportes/resumen").with(user(usuarioSinPermisos())))
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
