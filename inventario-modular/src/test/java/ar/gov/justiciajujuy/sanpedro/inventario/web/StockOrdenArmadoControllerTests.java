package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
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
class StockOrdenArmadoControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void cargaStockCreaOrdenYComparaGemeloDigital() throws Exception {
		String stock = """
				{
				  "tipo": "DISCO",
				  "estado": "DISPONIBLE",
				  "descripcion": "SSD nuevo para armado",
				  "marca": "Kingston",
				  "modelo": "SA400",
				  "serial": "DISK-001",
				  "capacidad": "480GB",
				  "ubicacion": "Deposito Informatica",
				  "observaciones": "Alta inicial de stock",
				  "activo": true,
				  "remito": "REM-2025-001",
				  "ordenCompra": "OC-2025-050",
				  "proveedor": "Banghó"
				}
				""";
		String orden = """
				{
				  "estado": "EN_ARMADO",
				  "descripcion": "Armado de PC-INF-001",
				  "observaciones": "Orden inicial para comparar con script"
				}
				""";
		String esperado = """
				{
				  "stockComponenteId": 2,
				  "tipo": "DISCO",
				  "descripcion": "Disco esperado desde stock",
				  "marca": "Kingston",
				  "modelo": "SA400",
				  "serial": "DISK-001",
				  "capacidad": "480GB",
				  "ubicacion": "SATA 1",
				  "observaciones": "Debe coincidir con el reporte"
				}
				""";
		String reporteScript = """
				{
				  "nombre": "PC-INF-001",
				  "fuero": "Informatica",
				  "procesador": "Intel Core i5",
				  "ramDetalles": "8GB DDR4",
				  "ramSeriales": "RAMSN-001",
				  "discosModelos": "SA400",
				  "discosSeriales": "DISK-001",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/stock/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(stock))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.serial").value("DISK-001"))
			.andExpect(jsonPath("$.remito").value("REM-2025-001"))
			.andExpect(jsonPath("$.ordenCompra").value("OC-2025-050"))
			.andExpect(jsonPath("$.proveedor").value("Banghó"));

		mockMvc.perform(post("/api/v1/equipos/1/ordenes-armado")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(orden))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.estado").value("EN_ARMADO"));

		mockMvc.perform(post("/api/v1/ordenes-armado/1/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(esperado))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.origen").value("ORDEN_ARMADO"))
			.andExpect(jsonPath("$.estadoComparacion").value("ESPERADO"))
			.andExpect(jsonPath("$.remito").value("REM-2025-001"))
			.andExpect(jsonPath("$.ordenCompra").value("OC-2025-050"))
			.andExpect(jsonPath("$.proveedor").value("Banghó"));

		mockMvc.perform(post("/api/v1/ordenes-armado/componentes/1/confirmar-salida-stock")
				.with(user(adminLocal()))
				.with(csrf()))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.origen").value("STOCK"))
			.andExpect(jsonPath("$.estadoComparacion").value("ESPERADO"))
			.andExpect(jsonPath("$.serial").value("DISK-001"))
			.andExpect(jsonPath("$.remito").value("REM-2025-001"));

		mockMvc.perform(get("/api/v1/stock/componentes").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.serial == 'DISK-001' && @.estado == 'ASIGNADO')]", hasSize(1)));

		mockMvc.perform(post("/api/v1/equipos/inventario")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(reporteScript))
			.andExpect(status().isCreated());

		mockMvc.perform(get("/api/v1/equipos/1/gemelo-digital/comparacion").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.resultado == 'COINCIDE')]", hasSize(1)))
			.andExpect(jsonPath("$[?(@.resultado == 'FALTA')]", hasSize(1)));
	}

	@Test
	void bloqueaStockSinPermiso() throws Exception {
		mockMvc.perform(get("/api/v1/stock/componentes").with(user(usuarioSinPermisos())))
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
