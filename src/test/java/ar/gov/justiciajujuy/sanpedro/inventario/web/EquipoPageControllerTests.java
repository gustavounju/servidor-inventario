package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrlPattern;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.view;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;

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
class EquipoPageControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void muestraListadoDeEquiposParaUsuariosConPermiso() throws Exception {
		mockMvc.perform(get("/admin/equipos").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/equipos"))
			.andExpect(content().string(containsString("Inventario tecnico")))
			.andExpect(content().string(containsString("Importar inventario viejo")))
			.andExpect(content().string(containsString("PC-INF-001")))
			.andExpect(content().string(containsString("Windows 11 Pro")));
	}

	@Test
	void filtraListadoDeEquiposDesdePantalla() throws Exception {
		mockMvc.perform(get("/admin/equipos")
				.param("q", "mesa")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("PC-MESA-002")));
	}

	@Test
	void muestraDetalleDeHardwareExtendido() throws Exception {
		mockMvc.perform(get("/admin/equipos/1").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Gemelo digital / Componentes")))
			.andExpect(content().string(containsString("Modulo RAM instalado")))
			.andExpect(content().string(containsString("Edicion manual controlada")))
			.andExpect(content().string(containsString("Detalle RAM")))
			.andExpect(content().string(containsString("KINGSTON SA400")))
			.andExpect(content().string(containsString("MB-001")));
	}

	@Test
	void agregaComponenteDesdeDetalleDeEquipo() throws Exception {
		mockMvc.perform(post("/admin/equipos/1/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.param("tipo", "MONITOR")
				.param("origen", "STOCK")
				.param("estadoComparacion", "ESPERADO")
				.param("descripcion", "Monitor entregado para armado")
				.param("marca", "Samsung")
				.param("modelo", "S24")
				.param("serial", "MON-001")
				.param("capacidad", "24 pulgadas")
				.param("ubicacion", "Escritorio")
				.param("observaciones", "Sale de stock")
				.param("activo", "true"))
			.andExpect(status().is3xxRedirection());

		mockMvc.perform(get("/admin/equipos/1").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Monitor entregado para armado")))
			.andExpect(content().string(containsString("MON-001")));
	}

	@Test
	void consolidaRelevamientoInicialDesdeDetalleDeEquipo() throws Exception {
		mockMvc.perform(post("/admin/equipos/1/componentes/consolidar-relevamiento-inicial")
				.with(user(adminLocal()))
				.with(csrf()))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/equipos/1?actualizado=*"));

		mockMvc.perform(get("/admin/equipos/1").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("RELEVAMIENTO_INICIAL")))
			.andExpect(content().string(containsString("Gemelo Digital")));
	}

	@Test
	void actualizaEquipoDesdePantalla() throws Exception {
		mockMvc.perform(post("/admin/equipos/1")
				.with(user(adminLocal()))
				.with(csrf())
				.param("nombre", "pc-inf-001-editada")
				.param("fuero", "Informatica")
				.param("ultimoUsuario", "soporte")
				.param("ip", "10.15.2.99")
				.param("sistemaOperativo", "Windows 11 Enterprise")
				.param("procesador", "Intel Core i7")
				.param("ramMb", "32768")
				.param("ramDetalles", "2x16GB DDR4")
				.param("ramSeriales", "RAM-A | RAM-B")
				.param("discosModelos", "WD Blue NVMe")
				.param("discosSeriales", "NVME-001")
				.param("motherboardModelo", "Dell Board X")
				.param("motherboardSerial", "MB-X")
				.param("monitores", "Dell 24 SN MON-X")
				.param("teclado", "Dell KB216")
				.param("mouse", "Dell MS116")
				.param("impresora", "Ricoh Informatica")
				.param("activo", "true"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/equipos/1?actualizado=*"));

		mockMvc.perform(get("/admin/equipos/1").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("PC-INF-001-EDITADA")))
			.andExpect(content().string(containsString("Windows 11 Enterprise")));
	}

	@Test
	void importaInventarioViejoDesdePantalla() throws Exception {
		String csv = """
				nombre,ultimoUsuario,fuero,ubicacion,ip,sistemaOperativo,procesador,ramMb
				pc-vieja-web-020,mesa,Informatica,Oficina Informatica,10.15.2.50,Windows 7 Pro,Intel Core 2 Duo,4096
				""";

		mockMvc.perform(post("/admin/equipos/importar-viejo")
				.with(user(adminLocal()))
				.with(csrf())
				.param("contenidoCsv", csv))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin/equipos"));

		mockMvc.perform(get("/admin/equipos")
				.param("q", "pc-vieja-web-020")
				.with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("PC-VIEJA-WEB-020")))
			.andExpect(content().string(containsString("Windows 7 Pro")));
	}

	@Test
	void muestraErrorSiElNombreYaExisteAlEditarDesdePantalla() throws Exception {
		mockMvc.perform(post("/admin/equipos/1")
				.with(user(adminLocal()))
				.with(csrf())
				.param("nombre", "PC-MESA-002")
				.param("fuero", "Informatica")
				.param("activo", "true"))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/equipo-detalle"))
			.andExpect(content().string(containsString("Ya existe un equipo con nombre")));
	}

	@Test
	void bloqueaPantallaDeEquiposSiNoTienePermiso() throws Exception {
		mockMvc.perform(get("/admin/equipos").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden());
	}

	@Test
	void bloqueaEdicionDeEquipoSiNoTienePermiso() throws Exception {
		mockMvc.perform(post("/admin/equipos/1")
				.with(user(usuarioSinPermisos()))
				.with(csrf())
				.param("nombre", "PC-INF-001")
				.param("fuero", "Informatica")
				.param("activo", "true"))
			.andExpect(status().isForbidden());
	}

	@Test
	void iniciaNuevoEquipoEnTallerConCodigoAutomaticoYRedirigeAOrdenes() throws Exception {
		mockMvc.perform(post("/admin/equipos/nuevo-taller")
				.with(user(adminLocal()))
				.with(csrf()))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/ordenes-armado?*equipoId=*&creado=1"));
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
