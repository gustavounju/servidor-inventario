package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.hasSize;
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
class EquipoControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void listaEquiposConPaginacionSiTienePermisoVer() throws Exception {
		mockMvc.perform(get("/api/v1/equipos").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.equipos", hasSize(2)))
			.andExpect(jsonPath("$.equipos[0].nombre").value("PC-INF-001"))
			.andExpect(jsonPath("$.paginacion.totalItems").value(2));
	}

	@Test
	void filtraEquiposPorNombreUsuarioOFuero() throws Exception {
		mockMvc.perform(get("/api/v1/equipos")
				.param("q", "mesa")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.equipos", hasSize(1)))
			.andExpect(jsonPath("$.equipos[0].nombre").value("PC-MESA-002"));
	}

	@Test
	void devuelveDetalleDeEquipo() throws Exception {
		mockMvc.perform(get("/api/v1/equipos/1").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.nombre").value("PC-INF-001"))
			.andExpect(jsonPath("$.procesador").value("Intel Core i5"))
			.andExpect(jsonPath("$.ramMb").value(16384))
			.andExpect(jsonPath("$.ramDetalles").value("2x8GB DDR4"))
			.andExpect(jsonPath("$.discosModelos").value("KINGSTON SA400"))
			.andExpect(jsonPath("$.motherboardSerial").value("MB-001"));
	}

	@Test
	void registraInventarioComoAltaOActualizacionDeEquipo() throws Exception {
		String body = """
				{
				  "nombre": "pc-nueva-003",
				  "ultimoUsuario": "jlopez",
				  "fuero": "Informatica",
				  "ip": "10.15.2.12",
				  "sistemaOperativo": "Windows 11 Pro",
				  "procesador": "AMD Ryzen 5",
				  "ramMb": 16384,
				  "ramDetalles": "2x8GB DDR4 3200MHz",
				  "ramSeriales": "RAM-001 | RAM-002",
				  "discosModelos": "WD Blue SSD",
				  "discosSeriales": "DISK-001",
				  "motherboardModelo": "ASUS PRIME",
				  "motherboardSerial": "MB-123",
				  "monitores": "Samsung 24 SN-456",
				  "teclado": "Logitech K120",
				  "mouse": "Logitech M90",
				  "impresora": "Ricoh Mesa",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/equipos/inventario")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(body))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.nombre").value("PC-NUEVA-003"))
			.andExpect(jsonPath("$.ultimoUsuario").value("jlopez"))
			.andExpect(jsonPath("$.ramDetalles").value("2x8GB DDR4 3200MHz"))
			.andExpect(jsonPath("$.discosSeriales").value("DISK-001"))
			.andExpect(jsonPath("$.monitores").value("Samsung 24 SN-456"))
			.andExpect(jsonPath("$.monitoreo").value("REPORTADO"));

		mockMvc.perform(get("/api/v1/equipos/3/componentes").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.origen == 'SCRIPT')]", hasSize(9)))
			.andExpect(jsonPath("$[?(@.serial == 'RAM-001' && @.estadoComparacion == 'DETECTADO')]", hasSize(1)))
			.andExpect(jsonPath("$[?(@.serial == 'DISK-001')]", hasSize(1)));
	}

	@Test
	void reemplazaComponentesDetectadosPorScriptAlRecibirNuevoReporte() throws Exception {
		String primerReporte = """
				{
				  "nombre": "pc-script-010",
				  "fuero": "Informatica",
				  "procesador": "Intel Core i5",
				  "ramDetalles": "8GB DDR4",
				  "ramSeriales": "RAM-UNO",
				  "discosModelos": "SSD Kingston",
				  "discosSeriales": "DISK-UNO",
				  "activo": true
				}
				""";
		String segundoReporte = """
				{
				  "nombre": "pc-script-010",
				  "fuero": "Informatica",
				  "procesador": "Intel Core i5",
				  "ramDetalles": "16GB DDR4",
				  "ramSeriales": "RAM-DOS",
				  "discosModelos": "SSD WD",
				  "discosSeriales": "DISK-DOS",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/equipos/inventario")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(primerReporte))
			.andExpect(status().isCreated());
		mockMvc.perform(post("/api/v1/equipos/inventario")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(segundoReporte))
			.andExpect(status().isCreated());

		mockMvc.perform(get("/api/v1/equipos")
				.param("q", "pc-script-010")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.equipos[0].nombre").value("PC-SCRIPT-010"));
		mockMvc.perform(get("/api/v1/equipos/3/componentes").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.origen == 'SCRIPT')]", hasSize(3)))
			.andExpect(jsonPath("$[?(@.serial == 'RAM-UNO')]", hasSize(0)))
			.andExpect(jsonPath("$[?(@.serial == 'RAM-DOS')]", hasSize(1)))
			.andExpect(jsonPath("$[?(@.serial == 'DISK-DOS')]", hasSize(1)));
	}

	@Test
	void actualizaEquipoManualmenteSiTienePermisoEditar() throws Exception {
		String body = """
				{
				  "nombre": "pc-inf-001-renombrada",
				  "ultimoUsuario": "soporte",
				  "fuero": "Informatica",
				  "ip": "10.15.2.99",
				  "sistemaOperativo": "Windows 11 Enterprise",
				  "procesador": "Intel Core i7",
				  "ramMb": 32768,
				  "ramDetalles": "2x16GB DDR4",
				  "ramSeriales": "RAM-A | RAM-B",
				  "discosModelos": "WD Blue NVMe",
				  "discosSeriales": "NVME-001",
				  "motherboardModelo": "Dell Board X",
				  "motherboardSerial": "MB-X",
				  "monitores": "Dell 24 SN MON-X",
				  "teclado": "Dell KB216",
				  "mouse": "Dell MS116",
				  "impresora": "Ricoh Informatica",
				  "activo": true
				}
				""";

		mockMvc.perform(put("/api/v1/equipos/1")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(body))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.nombre").value("PC-INF-001-RENOMBRADA"))
			.andExpect(jsonPath("$.ultimoUsuario").value("soporte"))
			.andExpect(jsonPath("$.ramMb").value(32768))
			.andExpect(jsonPath("$.motherboardSerial").value("MB-X"));
	}

	@Test
	void rechazaActualizacionManualConNombreDuplicado() throws Exception {
		String body = """
				{
				  "nombre": "PC-MESA-002",
				  "fuero": "Informatica",
				  "activo": true
				}
				""";

		mockMvc.perform(put("/api/v1/equipos/1")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(body))
			.andExpect(status().isConflict());
	}

	@Test
	void desactivaEquipoSinPerderEstadoDeMonitoreo() throws Exception {
		String body = """
				{
				  "nombre": "PC-INF-001",
				  "fuero": "Informatica",
				  "activo": false
				}
				""";

		mockMvc.perform(put("/api/v1/equipos/1")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(body))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.activo").value(false))
			.andExpect(jsonPath("$.monitoreo").value("REPORTADO"));
	}

	@Test
	void registraInventarioApiConTokenDeMaquina() throws Exception {
		String body = """
				{
				  "nombre": "pc-token-005",
				  "ultimoUsuario": "script",
				  "ip": "192.168.1.50",
				  "sistemaOperativo": "Windows 11 Pro",
				  "procesador": "Intel Core i5",
				  "ramMb": 8192,
				  "impresora": "HP Oficina",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/equipos/inventario")
				.header("Authorization", "Bearer dev-token-123456")
				.contentType(MediaType.APPLICATION_JSON)
				.content(body))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.nombre").value("PC-TOKEN-005"))
			.andExpect(jsonPath("$.monitoreo").value("REPORTADO"));
	}

	@Test
	void importaInventarioViejoDesdeCsv() throws Exception {
		String csv = """
				PC_Nombre;Usuario_Actual;fuero;ubicacion;IPAddress;OsName;Procesador;RAM (GB);RAM_Detalles;RAM_Serials;Disk_Models;Disk_Serials
				pc-vieja-010;mrojas;Informatica;Oficina Informatica;10.15.2.40;Windows 7 Pro;Intel Core i3;4;4GB DDR3;RAM-OLD-010;WD HDD;DISK-OLD-010
				""";

		mockMvc.perform(post("/api/v1/equipos/importar-viejo")
				.with(user(adminLocal()))
				.with(csrf())
				.contentType(MediaType.parseMediaType("text/csv"))
				.content(csv))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.procesados").value(1))
			.andExpect(jsonPath("$.importados").value(1))
			.andExpect(jsonPath("$.errores", hasSize(0)));

		mockMvc.perform(get("/api/v1/equipos")
				.param("q", "pc-vieja-010")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.equipos[0].nombre").value("PC-VIEJA-010"))
			.andExpect(jsonPath("$.equipos[0].ubicacion").value("Oficina Informatica"));
	}

	@Test
	void bloqueaUsuariosSinPermisoParaVerEquipos() throws Exception {
		mockMvc.perform(get("/api/v1/equipos").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden());
	}

	@Test
	void bloqueaUsuariosSinPermisoParaRegistrarInventario() throws Exception {
		String body = """
				{
				  "nombre": "pc-bloqueada",
				  "fuero": "Informatica",
				  "activo": true
				}
				""";

		mockMvc.perform(post("/api/v1/equipos/inventario")
				.with(user(usuarioSinPermisos()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(body))
			.andExpect(status().isForbidden());
	}

	@Test
	void bloqueaUsuariosSinPermisoParaActualizarEquipo() throws Exception {
		String body = """
				{
				  "nombre": "PC-INF-001",
				  "fuero": "Informatica",
				  "activo": true
				}
				""";

		mockMvc.perform(put("/api/v1/equipos/1")
				.with(user(usuarioSinPermisos()))
				.with(csrf())
				.contentType(MediaType.APPLICATION_JSON)
				.content(body))
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

	@Test
	void registraInventarioLegacyConTokenValidoYFormatoHeredado() throws Exception {
		String legacyPayload = """
				{
				  "PC_Nombre": "pc-legacy-004",
				  "Usuario_Actual": "mperes",
				  "Sistema": {
				    "OsName": "Windows 10 Pro",
				    "Procesador": "Intel Core i7",
				    "RAM (GB)": 8.0,
				    "Office": "Microsoft Office 2019"
				  },
				  "Red": [
				    { "IPAddress": "10.15.2.14", "MACAddress": "00:11:22:33:44:55" }
				  ],
				  "Printer_Model": "HP LaserJet Legacy",
				  "Printer_Port": "USB001 (Local)",
				  "Printer_SN": "SN-LEGACY-123",
				  "RAM_Detalles": "8GB DDR4 2666MHz",
				  "RAM_Serials": "RAM-LEGACY-001",
				  "Disk_Models": "KINGSTON SSD",
				  "Disk_Serials": "DISK-LEGACY-001",
				  "Motherboard_Model": "Dell Board",
				  "Motherboard_SN": "MB-LEGACY-001",
				  "Monitors": "Dell 22 MON-001",
				  "Keyboard_Model": "Dell Keyboard",
				  "Mouse_Model": "Dell Mouse"
				}
				""";

		mockMvc.perform(post("/submit_inventory")
				.header("Authorization", "Bearer dev-token-123456")
				.contentType(MediaType.APPLICATION_JSON)
				.content(legacyPayload))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.status").value("success"));

		mockMvc.perform(get("/api/v1/equipos")
				.param("q", "pc-legacy-004")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.equipos[0].nombre").value("PC-LEGACY-004"));

		mockMvc.perform(get("/api/v1/equipos/3/componentes").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$[?(@.origen == 'SCRIPT')]", hasSize(8)))
			.andExpect(jsonPath("$[?(@.serial == 'DISK-LEGACY-001')]", hasSize(1)))
			.andExpect(jsonPath("$[?(@.serial == 'MB-LEGACY-001')]", hasSize(1)));
	}

	@Test
	void rechazaInventarioLegacyConTokenInvalido() throws Exception {
		mockMvc.perform(post("/submit_inventory")
				.header("Authorization", "Bearer token-invalido")
				.contentType(MediaType.APPLICATION_JSON)
				.content("{}"))
			.andExpect(status().isUnauthorized());
	}
}
