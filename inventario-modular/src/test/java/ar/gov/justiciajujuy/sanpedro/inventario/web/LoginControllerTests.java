package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.matchesPattern;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.view;

import java.security.MessageDigest;
import java.util.HexFormat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.core.io.ClassPathResource;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class LoginControllerTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	void muestraComandoDeInventarioParaCopiarDesdeLogin() throws Exception {
		mockMvc.perform(get("/login"))
			.andExpect(status().isOk())
			.andExpect(view().name("login"))
			.andExpect(content().string(containsString("Usuario")))
			.andExpect(content().string(containsString("Clave")))
			.andExpect(content().string(containsString("Ingresar")))
			.andExpect(content().string(containsString("Copiar comando")))
			.andExpect(content().string(containsString("inventory-command")))
			.andExpect(content().string(containsString("/scripts/windows/inventario-modular.ps1")))
			.andExpect(content().string(containsString("/scripts/windows/inventario-modular.ps1.sha256")))
			.andExpect(content().string(containsString("New-Object Net.WebClient")))
			.andExpect(content().string(containsString("SHA-256 invalido")))
			.andExpect(content().string(containsString("-ExecutionPolicy Bypass")))
			.andExpect(content().string(containsString("/api/v1/equipos/inventario")));
	}

	@Test
	void permiteDescargarScriptDeInventarioSinLogin() throws Exception {
		mockMvc.perform(get("/scripts/windows/inventario-modular.ps1"))
			.andExpect(status().isOk())
			.andExpect(content().string(containsString("param(")))
			.andExpect(content().string(containsString("Get-WmiObject")))
			.andExpect(content().string(containsString("Test-HasText")))
			.andExpect(content().string(containsString("discosModelos")))
			.andExpect(content().string(containsString("motherboardSerial")));
	}

	@Test
	void publicaSha256DelScriptDeInventarioSinLogin() throws Exception {
		mockMvc.perform(get("/scripts/windows/inventario-modular.ps1.sha256"))
			.andExpect(status().isOk())
			.andExpect(content().string(matchesPattern("(?s)^[a-f0-9]{64}\\R?$")));
	}

	@Test
	void sha256PublicadoCoincideConElScriptServido() throws Exception {
		String hashPublicado = mockMvc.perform(get("/scripts/windows/inventario-modular.ps1.sha256"))
			.andReturn()
			.getResponse()
			.getContentAsString()
			.trim();
		byte[] scriptBytes = new ClassPathResource("static/scripts/windows/inventario-modular.ps1")
			.getInputStream()
			.readAllBytes();
		String hashReal = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(scriptBytes));

		assertThat(hashPublicado).isEqualTo(hashReal);
	}
}
