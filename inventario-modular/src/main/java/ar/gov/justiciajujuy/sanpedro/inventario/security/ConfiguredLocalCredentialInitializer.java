package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import javax.sql.DataSource;

import ar.gov.justiciajujuy.sanpedro.inventario.config.LocalAuthenticationProperties;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(name = {
		"inventario.local-auth.enabled",
		"inventario.local-db-auth.enabled"
}, havingValue = "true")
public class ConfiguredLocalCredentialInitializer implements ApplicationRunner {

	private final LocalAuthenticationProperties properties;
	private final UsuarioSistemaRepository usuarioSistemaRepository;
	private final CredencialLocalRepository credencialLocalRepository;
	private final PasswordEncoder passwordEncoder;
	private final DataSource dataSource;

	public ConfiguredLocalCredentialInitializer(
			LocalAuthenticationProperties properties,
			UsuarioSistemaRepository usuarioSistemaRepository,
			CredencialLocalRepository credencialLocalRepository,
			PasswordEncoder passwordEncoder,
			DataSource dataSource) {
		this.properties = properties;
		this.usuarioSistemaRepository = usuarioSistemaRepository;
		this.credencialLocalRepository = credencialLocalRepository;
		this.passwordEncoder = passwordEncoder;
		this.dataSource = dataSource;
	}

	@Override
	public void run(ApplicationArguments args) {
		if (!tableExists("usuarios") || !tableExists("credenciales_locales")) {
			return;
		}
		if (credencialLocalRepository.existsByUsuarioUsernameIgnoreCase(properties.getUsername())) {
			return;
		}
		usuarioSistemaRepository.findByUsernameIgnoreCase(properties.getUsername())
			.filter(usuario -> usuario.getOrigen() == OrigenIdentidad.LOCAL)
			.ifPresent(usuario -> credencialLocalRepository.save(new CredencialLocal(
					usuario,
					passwordEncoder.encode(properties.getPassword()),
					false)));
	}

	private boolean tableExists(String tableName) {
		try (Connection connection = dataSource.getConnection();
				ResultSet tables = connection.getMetaData().getTables(null, null, tableName, null)) {
			if (tables.next()) {
				return true;
			}
		} catch (SQLException ex) {
			return false;
		}
		try (Connection connection = dataSource.getConnection();
				ResultSet tables = connection.getMetaData().getTables(null, null, tableName.toUpperCase(), null)) {
			return tables.next();
		} catch (SQLException ex) {
			return false;
		}
	}
}
