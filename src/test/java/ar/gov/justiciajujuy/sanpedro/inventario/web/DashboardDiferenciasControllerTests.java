package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.not;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
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
class DashboardDiferenciasControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void resumeDiferenciasDelGemeloDigital() throws Exception {
		mockMvc.perform(get("/api/v1/gemelo-digital/dashboard-diferencias").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.conteo.falta").value(1))
			.andExpect(jsonPath("$.conteo.sobra").value(1))
			.andExpect(jsonPath("$.conteo.revisar").value(0))
			.andExpect(jsonPath("$.conteo.coincide").value(0))
			.andExpect(jsonPath("$.conteo.pendientes").value(2))
			.andExpect(jsonPath("$.equipos", hasSize(1)))
			.andExpect(jsonPath("$.equipos[0].equipoId").value(1))
			.andExpect(jsonPath("$.equipos[0].equipoNombre").value("PC-INF-001"))
			.andExpect(jsonPath("$.equipos[0].diferencias", hasSize(2)));
	}

	@Test
	void filtraDiferenciasPorEstadoEquipoYFuero() throws Exception {
		mockMvc.perform(get("/api/v1/gemelo-digital/dashboard-diferencias")
				.param("estado", "FALTA")
				.param("equipo", "inf")
				.param("fuero", "informatica")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.conteo.falta").value(1))
			.andExpect(jsonPath("$.conteo.sobra").value(0))
			.andExpect(jsonPath("$.conteo.revisar").value(0))
			.andExpect(jsonPath("$.conteo.coincide").value(0))
			.andExpect(jsonPath("$.equipos", hasSize(1)))
			.andExpect(jsonPath("$.equipos[0].diferencias", hasSize(1)))
			.andExpect(jsonPath("$.equipos[0].diferencias[0].resultado").value("FALTA"));
	}

	@Test
	void exportaDiferenciasFiltradasComoCsv() throws Exception {
		mockMvc.perform(get("/api/v1/gemelo-digital/dashboard-diferencias.csv")
				.param("estado", "FALTA")
				.param("equipo", "inf")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("equipo,fuero,tipo,resultado,esperado,detectado,observacion")))
			.andExpect(content().string(containsString("PC-INF-001")))
			.andExpect(content().string(containsString("FALTA")))
			.andExpect(content().string(not(containsString("SOBRA"))));
	}

	@Test
	void muestraPantallaDeDiferenciasConAccesoAlEquipo() throws Exception {
		mockMvc.perform(get("/admin/dashboard-diferencias").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/dashboard-diferencias"))
			.andExpect(content().string(containsString("Dashboard de diferencias")))
			.andExpect(content().string(containsString("name=\"equipo\"")))
			.andExpect(content().string(containsString("name=\"fuero\"")))
			.andExpect(content().string(containsString("name=\"estado\"")))
			.andExpect(content().string(containsString("/api/v1/gemelo-digital/dashboard-diferencias.csv")))
			.andExpect(content().string(containsString("PC-INF-001")))
			.andExpect(content().string(containsString("href=\"/admin/equipos/1\"")));
	}

	@Test
	void bloqueaDashboardSiNoTienePermisoComponentes() throws Exception {
		mockMvc.perform(get("/api/v1/gemelo-digital/dashboard-diferencias").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden());
		mockMvc.perform(get("/admin/dashboard-diferencias").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden())
			.andExpect(content().string(not(containsString("Dashboard de diferencias"))));
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
