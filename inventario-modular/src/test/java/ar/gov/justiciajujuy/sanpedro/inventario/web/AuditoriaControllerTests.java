package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.not;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
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
class AuditoriaControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void registraYListaEventosDeAuditoria() throws Exception {
		String stock = """
				{
				  "tipo": "RAM",
				  "estado": "DISPONIBLE",
				  "descripcion": "Memoria para auditar",
				  "marca": "Kingston",
				  "modelo": "DDR4",
				  "serial": "AUD-RAM-001",
				  "capacidad": "8GB",
				  "ubicacion": "Deposito",
				  "observaciones": "Alta auditada",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/stock/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(stock))
			.andExpect(status().isCreated());

		mockMvc.perform(get("/api/v1/auditoria/eventos").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$", hasSize(1)))
			.andExpect(jsonPath("$[0].usuario").value("admin.local"))
			.andExpect(jsonPath("$[0].modulo").value("STOCK"))
			.andExpect(jsonPath("$[0].accion").value("CREAR"))
			.andExpect(jsonPath("$[0].entidadTipo").value("StockComponente"));

		mockMvc.perform(get("/api/v1/auditoria/eventos")
				.param("usuario", "admin")
				.param("modulo", "STOCK")
				.param("accion", "CREAR")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$", hasSize(1)))
			.andExpect(jsonPath("$[0].modulo").value("STOCK"));

		mockMvc.perform(get("/api/v1/auditoria/eventos.csv")
				.param("modulo", "STOCK")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(org.hamcrest.Matchers.containsString("id,fecha,usuario,modulo,accion,entidadTipo,entidadId,detalle")))
			.andExpect(content().string(org.hamcrest.Matchers.containsString("admin.local,STOCK,CREAR,StockComponente")));
	}

	@Test
	void muestraPantallaDeAuditoria() throws Exception {
		mockMvc.perform(get("/admin/auditoria").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/auditoria"))
			.andExpect(content().string(org.hamcrest.Matchers.containsString("Eventos recientes")))
			.andExpect(content().string(org.hamcrest.Matchers.containsString("name=\"usuario\"")))
			.andExpect(content().string(org.hamcrest.Matchers.containsString("name=\"modulo\"")))
			.andExpect(content().string(org.hamcrest.Matchers.containsString("name=\"accion\"")))
			.andExpect(content().string(org.hamcrest.Matchers.containsString("/api/v1/auditoria/eventos.csv")));
	}

	@Test
	void bloqueaAuditoriaSiNoTienePermiso() throws Exception {
		mockMvc.perform(get("/api/v1/auditoria/eventos").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden());
		mockMvc.perform(get("/admin/auditoria").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden())
			.andExpect(content().string(not(org.hamcrest.Matchers.containsString("Eventos recientes"))));
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
