package ar.gov.justiciajujuy.sanpedro.inventario.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestBuilders.formLogin;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Set;

import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService.CrearUsuarioCommand;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(properties = {
		"inventario.local-auth.enabled=true",
		"inventario.local-auth.username=admin.local",
		"inventario.local-auth.password=AdminLocal123",
		"inventario.local-db-auth.enabled=true"
})
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Sql(scripts = "/sql/limpiar-seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@Sql(scripts = "/sql/seguridad-modular-test.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
class DatabaseLocalAuthenticationProviderTests {

	@Autowired
	private MockMvc mockMvc;

	@Autowired
	private UsuarioManagementService usuarioManagementService;

	@Autowired
	private CredencialLocalRepository credencialLocalRepository;

	@Autowired
	private PasswordEncoder passwordEncoder;

	@Autowired
	private ConfiguredLocalCredentialInitializer configuredLocalCredentialInitializer;

	@Test
	void autenticaUsuarioLocalGuardadoEnBaseSinGuardarPasswordPlano() throws Exception {
		usuarioManagementService.crearUsuario(new CrearUsuarioCommand(
				"chofer.local",
				"Chofer de Guardia",
				"Servicios Generales",
				"LOCAL",
				"ChoferLocal123",
				true,
				Set.of("ADMINISTRADOR")));

		CredencialLocal credencial = credencialLocalRepository.findActivaByUsername("chofer.local").orElseThrow();
		assertThat(credencial.getPasswordHash()).isNotEqualTo("ChoferLocal123");
		assertThat(passwordEncoder.matches("ChoferLocal123", credencial.getPasswordHash())).isTrue();

		mockMvc.perform(formLogin()
				.user("chofer.local")
				.password("ChoferLocal123"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin"));
	}

	@Test
	void conviveUsuarioSimuladoConUsuariosLocalesDeBase() throws Exception {
		usuarioManagementService.crearUsuario(new CrearUsuarioCommand(
				"chofer.local",
				"Chofer de Guardia",
				"Servicios Generales",
				"LOCAL",
				"ChoferLocal123",
				true,
				Set.of("ADMINISTRADOR")));

		mockMvc.perform(formLogin()
				.user("admin.local")
				.password("AdminLocal123"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin"));

		mockMvc.perform(formLogin()
				.user("chofer.local")
				.password("ChoferLocal123"))
			.andExpect(status().is3xxRedirection())
			.andExpect(redirectedUrl("/admin"));
	}

	@Test
	void inicializaCredencialDelUsuarioConfiguradoSiExisteEnBase() throws Exception {
		configuredLocalCredentialInitializer.run(null);

		CredencialLocal credencial = credencialLocalRepository.findActivaByUsername("admin.local").orElseThrow();

		assertThat(credencial.getPasswordHash()).isNotEqualTo("AdminLocal123");
		assertThat(passwordEncoder.matches("AdminLocal123", credencial.getPasswordHash())).isTrue();
	}
}
