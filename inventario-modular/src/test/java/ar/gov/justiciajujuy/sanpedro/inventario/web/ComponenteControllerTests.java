package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.is;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
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
class ComponenteControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void listaComponentesDelGemeloDigital() throws Exception {
		mockMvc.perform(get("/api/v1/equipos/1/componentes").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$", hasSize(2)))
			.andExpect(jsonPath("$[0].tipo").value("DISCO"))
			.andExpect(jsonPath("$[1].tipo").value("RAM"));
	}

	@Test
	void creaComponenteParaEquipo() throws Exception {
		String body = """
				{
				  "tipo": "MONITOR",
				  "origen": "STOCK",
				  "estadoComparacion": "ESPERADO",
				  "descripcion": "Monitor entregado para armado",
				  "marca": "Samsung",
				  "modelo": "S24",
				  "serial": "MON-001",
				  "capacidad": "24 pulgadas",
				  "ubicacion": "Escritorio",
				  "observaciones": "Sale de stock para comparar contra equipo armado",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/equipos/1/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(body))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.tipo").value("MONITOR"))
			.andExpect(jsonPath("$.origen").value("STOCK"))
			.andExpect(jsonPath("$.estadoComparacion").value("ESPERADO"))
			.andExpect(jsonPath("$.serial").value("MON-001"));
	}

	@Test
	void actualizaComponenteExistente() throws Exception {
		String body = """
				{
				  "tipo": "RAM",
				  "origen": "SCRIPT",
				  "estadoComparacion": "COINCIDE",
				  "descripcion": "Modulo RAM verificado",
				  "marca": "Kingston",
				  "modelo": "DDR4 2666",
				  "serial": "RAMSN-001",
				  "capacidad": "8GB",
				  "ubicacion": "Slot 1",
				  "observaciones": "Comparado contra orden de armado",
				  "activo": true
				}
				""";

		mockMvc.perform(put("/api/v1/componentes/1")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(body))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.descripcion").value("Modulo RAM verificado"))
			.andExpect(jsonPath("$.observaciones").value("Comparado contra orden de armado"));
	}

	@Test
	void consolidaComponentesDetectadosComoRelevamientoInicial() throws Exception {
		mockMvc.perform(post("/api/v1/equipos/1/componentes/consolidar-relevamiento-inicial")
				.with(user(adminLocal()))
				.with(csrf()))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$", hasSize(3)))
			.andExpect(jsonPath("$[2].origen").value("RELEVAMIENTO_INICIAL"))
			.andExpect(jsonPath("$[2].estadoComparacion").value("ESPERADO"))
			.andExpect(jsonPath("$[2].serial").value("RAMSN-001"))
			.andExpect(jsonPath("$[2].observaciones").value("Consolidado como relevamiento inicial desde la ultima lectura del script. Observacion original: Detectado por script"));
	}

	@Test
	void comparaGemeloDigitalSinReutilizarDetectados() throws Exception {
		String detectado = """
				{
				  "tipo": "RAM",
				  "origen": "SCRIPT",
				  "estadoComparacion": "DETECTADO",
				  "descripcion": "Modulo RAM detectado",
				  "marca": "Kingston",
				  "modelo": "DDR4 2666",
				  "serial": "RAMSN-001",
				  "capacidad": "8GB",
				  "ubicacion": "Slot 1",
				  "observaciones": "Detectado por script",
				  "activo": true
				}
				""";
		String esperadoUno = """
				{
				  "tipo": "RAM",
				  "origen": "ORDEN_ARMADO",
				  "estadoComparacion": "ESPERADO",
				  "descripcion": "Primer modulo RAM esperado",
				  "marca": "Kingston",
				  "modelo": "DDR4 2666",
				  "serial": "RAMSN-001",
				  "capacidad": "8GB",
				  "ubicacion": "Slot 1",
				  "observaciones": "Debe coincidir con el script",
				  "activo": true
				}
				""";
		String esperadoDos = """
				{
				  "tipo": "RAM",
				  "origen": "ORDEN_ARMADO",
				  "estadoComparacion": "ESPERADO",
				  "descripcion": "Segundo modulo RAM esperado",
				  "marca": "Kingston",
				  "modelo": "DDR4 2666",
				  "serial": "RAMSN-002",
				  "capacidad": "8GB",
				  "ubicacion": "Slot 2",
				  "observaciones": "Debe aparecer como faltante si el script no lo detecto",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/equipos/2/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(detectado))
			.andExpect(status().isCreated());
		mockMvc.perform(post("/api/v1/equipos/2/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(esperadoUno))
			.andExpect(status().isCreated());
		mockMvc.perform(post("/api/v1/equipos/2/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(esperadoDos))
			.andExpect(status().isCreated());

		mockMvc.perform(get("/api/v1/equipos/2/gemelo-digital/comparacion").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.resultado == 'COINCIDE')]", hasSize(1)))
			.andExpect(jsonPath("$[?(@.resultado == 'FALTA')]", hasSize(1)))
			.andExpect(jsonPath("$[?(@.resultado == 'SOBRA')]", hasSize(0)));
	}

	@Test
	void marcaRevisionCuandoHayDatoParecidoPeroNoSeguro() throws Exception {
		String esperado = """
				{
				  "tipo": "DISCO",
				  "origen": "ORDEN_ARMADO",
				  "estadoComparacion": "ESPERADO",
				  "descripcion": "SSD Kingston esperado",
				  "marca": "Kingston",
				  "modelo": "SA400",
				  "serial": "DISK-REV-001",
				  "capacidad": "480GB",
				  "ubicacion": "SATA 1",
				  "observaciones": "Serial esperado distinto al detectado",
				  "activo": true
				}
				""";
		String detectado = """
				{
				  "tipo": "DISCO",
				  "origen": "SCRIPT",
				  "estadoComparacion": "DETECTADO",
				  "descripcion": "SSD Kingston detectado",
				  "marca": "Kingston",
				  "modelo": "Kingston SA400",
				  "serial": "DISK-OTRO",
				  "capacidad": "480GB",
				  "ubicacion": "SATA 1",
				  "observaciones": "Detectado por script",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/equipos/2/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(esperado))
			.andExpect(status().isCreated());
		mockMvc.perform(post("/api/v1/equipos/2/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(detectado))
			.andExpect(status().isCreated());

		mockMvc.perform(get("/api/v1/equipos/2/gemelo-digital/comparacion").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$", hasSize(1)))
			.andExpect(jsonPath("$[0].resultado", is("REVISAR")));
	}

	@Test
	void bloqueaComponentesSiNoTienePermiso() throws Exception {
		mockMvc.perform(get("/api/v1/equipos/1/componentes").with(user(usuarioSinPermisos())))
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
