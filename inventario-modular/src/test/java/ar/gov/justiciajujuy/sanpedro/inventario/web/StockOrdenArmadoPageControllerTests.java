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
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Sql(scripts = "/sql/limpiar-seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@Sql(scripts = "/sql/seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
class StockOrdenArmadoPageControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void muestraPantallaDeStockYCargaComponente() throws Exception {
		mockMvc.perform(get("/admin/stock").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/stock"))
			.andExpect(content().string(containsString("Componentes disponibles")))
			.andExpect(content().string(containsString("Memoria RAM nueva para armado")));

		mockMvc.perform(post("/admin/stock/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.param("tipo", "DISCO")
				.param("estado", "DISPONIBLE")
				.param("descripcion", "SSD disponible para armado")
				.param("marca", "Kingston")
				.param("modelo", "SA400")
				.param("serial", "WEB-DISK-001")
				.param("capacidad", "480GB")
				.param("ubicacion", "Deposito")
				.param("observaciones", "Carga desde pantalla")
				.param("activo", "true"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/stock?creado=*"));

		mockMvc.perform(get("/admin/stock").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("WEB-DISK-001")));
	}

	@Test
	void editaStockDesdePantalla() throws Exception {
		mockMvc.perform(post("/admin/stock/componentes/1")
				.with(user(adminLocal()))
				.with(csrf())
				.param("tipo", "RAM")
				.param("estado", "BAJA")
				.param("descripcion", "Memoria RAM revisada")
				.param("marca", "Kingston")
				.param("modelo", "DDR4 3200")
				.param("serial", "STOCK-RAM-EDITADA")
				.param("capacidad", "16GB")
				.param("ubicacion", "Deposito baja")
				.param("observaciones", "Actualizada desde pantalla")
				.param("activo", "true"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/stock?creado=*"));

		mockMvc.perform(get("/admin/stock").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Memoria RAM revisada")))
			.andExpect(content().string(containsString("STOCK-RAM-EDITADA")))
			.andExpect(content().string(containsString("BAJA")));
	}

	@Test
	void muestraPantallaDeOrdenesYCargaComponenteEsperado() throws Exception {
		mockMvc.perform(get("/admin/ordenes-armado").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(view().name("admin/ordenes-armado"))
			.andExpect(content().string(containsString("Equipo de trabajo")))
			.andExpect(content().string(containsString("Crear orden")));

		mockMvc.perform(post("/admin/ordenes-armado")
				.with(user(adminLocal()))
				.with(csrf())
				.param("equipoId", "1")
				.param("estado", "EN_ARMADO")
				.param("descripcion", "Orden web para PC-INF-001")
				.param("observaciones", "Prueba de pantalla"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/ordenes-armado?equipoId=1&creado=*"));

		mockMvc.perform(post("/admin/ordenes-armado/1/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.param("equipoId", "1")
				.param("stockComponenteId", "1")
				.param("tipo", "RAM")
				.param("descripcion", "RAM esperada desde pantalla")
				.param("marca", "Kingston")
				.param("modelo", "DDR4 2666")
				.param("serial", "STOCK-RAM-001")
				.param("capacidad", "8GB")
				.param("ubicacion", "Slot 1")
				.param("observaciones", "Reserva desde stock"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/ordenes-armado?equipoId=1&creado=*"));

		mockMvc.perform(get("/admin/ordenes-armado?equipoId=1").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Componentes de orden")))
			.andExpect(content().string(containsString("Confirmar salida")))
			.andExpect(content().string(containsString("RESERVADO")));

		mockMvc.perform(post("/admin/ordenes-armado/componentes/1/confirmar-salida-stock")
				.with(user(adminLocal()))
				.with(csrf())
				.param("equipoId", "1"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/ordenes-armado?equipoId=1&creado=*"));

		mockMvc.perform(get("/admin/stock").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("ASIGNADO")));

		mockMvc.perform(get("/admin/equipos/1").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("RAM esperada desde pantalla")))
			.andExpect(content().string(containsString("STOCK")))
			.andExpect(content().string(containsString("Comparacion del gemelo digital")));
	}

	@Test
	void editaOrdenYPermiteElegirOrdenParaComponenteEsperado() throws Exception {
		mockMvc.perform(post("/admin/ordenes-armado")
				.with(user(adminLocal()))
				.with(csrf())
				.param("equipoId", "1")
				.param("estado", "BORRADOR")
				.param("descripcion", "Orden uno")
				.param("observaciones", "Primera orden"))
			.andExpect(status().is3xxRedirection());
		mockMvc.perform(post("/admin/ordenes-armado")
				.with(user(adminLocal()))
				.with(csrf())
				.param("equipoId", "1")
				.param("estado", "BORRADOR")
				.param("descripcion", "Orden dos")
				.param("observaciones", "Segunda orden"))
			.andExpect(status().is3xxRedirection());

		mockMvc.perform(post("/admin/ordenes-armado/1")
				.with(user(adminLocal()))
				.with(csrf())
				.param("equipoId", "1")
				.param("estado", "ESPERANDO_REPORTE")
				.param("descripcion", "Orden uno editada")
				.param("observaciones", "Esperando script"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/ordenes-armado?equipoId=1&creado=*"));

		mockMvc.perform(post("/admin/ordenes-armado/componentes")
				.with(user(adminLocal()))
				.with(csrf())
				.param("equipoId", "1")
				.param("ordenId", "1")
				.param("tipo", "DISCO")
				.param("descripcion", "Disco esperado en orden elegida")
				.param("marca", "WD")
				.param("modelo", "Blue")
				.param("serial", "ORDEN-UNO-DISCO")
				.param("capacidad", "1TB")
				.param("ubicacion", "NVMe")
				.param("observaciones", "Cargado eligiendo orden"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrlPattern("/admin/ordenes-armado?equipoId=1&creado=*"));

		mockMvc.perform(get("/admin/ordenes-armado?equipoId=1").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Orden uno editada")))
			.andExpect(content().string(containsString("ESPERANDO_REPORTE")));

		mockMvc.perform(get("/admin/equipos/1").with(user(adminLocal())))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("Disco esperado en orden elegida")))
			.andExpect(content().string(containsString("ORDEN-UNO-DISCO")));
	}

	@Test
	void bloqueaPantallasSiNoTienePermisos() throws Exception {
		mockMvc.perform(get("/admin/stock").with(user(usuarioSinPermisos())))
			.andExpect(status().isForbidden());
		mockMvc.perform(get("/admin/ordenes-armado").with(user(usuarioSinPermisos())))
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
