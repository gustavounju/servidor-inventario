package ar.gov.justiciajujuy.sanpedro.inventario.config;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.sql.DataSource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Profile;

@Configuration
@Profile("local")
public class DataSourceConfig {

	private static final Logger log = LoggerFactory.getLogger(DataSourceConfig.class);

	@Value("${inventario.datasource.primary.url:jdbc:mysql://10.15.0.62:3306/inventario_modular}")
	private String primaryUrl;

	@Value("${inventario.datasource.primary.username:inventario_modular_app}")
	private String primaryUsername;

	@Value("${inventario.datasource.primary.password:}")
	private String primaryPassword;

	@Value("${inventario.datasource.fallback.url:jdbc:mysql://127.0.0.1:3306/inventario_modular}")
	private String fallbackUrl;

	@Value("${inventario.datasource.fallback.username:inventario_local}")
	private String fallbackUsername;

	@Value("${inventario.datasource.fallback.password:Cambiar_Clave_Local_123!}")
	private String fallbackPassword;

	@Value("${inventario.datasource.timeout-ms:1500}")
	private int timeoutMs;

	@Bean
	@Primary
	public DataSource dataSource() {
		log.info("Iniciando verificacion de conexion a base de datos principal en MySQL...");
		
		HostPort hostPort = parseHostPort(primaryUrl);
		boolean primaryReachable = false;
		String urlToUse = primaryUrl;
		
		if (hostPort != null) {
			primaryReachable = isReachable(hostPort.host, hostPort.port, timeoutMs);
			
		}

		if (primaryReachable) {
			HostPort activeHostPort = parseHostPort(urlToUse);
			String activeHost = activeHostPort != null ? activeHostPort.host : "desconocido";
			int activePort = activeHostPort != null ? activeHostPort.port : 3306;
			log.info("Base de datos principal (MySQL {}:{}) ALCANZABLE. Conectando a: {}", 
					activeHost, activePort, urlToUse);
			try {
				DataSource ds = DataSourceBuilder.create()
						.url(urlToUse)
						.username(primaryUsername)
						.password(primaryPassword)
						.driverClassName("com.mysql.cj.jdbc.Driver")
						.build();
				// Hacemos una prueba rapida de conexion real antes de entregar el bean
				try (java.sql.Connection conn = ds.getConnection()) {
					log.info("Conexion establecida exitosamente a la base de datos principal MySQL.");
					return ds;
				}
			} catch (Exception e) {
				log.warn("Fallo el login o establecimiento de sesion en MySQL de produccion ({}). Rebotando a base local...", e.getMessage());
			}
		} else {
			if (hostPort != null) {
				log.warn("Base de datos principal (MySQL {}:{}) INALCANZABLE (Timeout {} ms).", 
						hostPort.host, hostPort.port, timeoutMs);
			} else {
				log.warn("URL principal no valida para analisis de host/puerto: {}.", primaryUrl);
			}
		}

		log.info("Usando base de datos MySQL local como fallback. Conectando a: {}", fallbackUrl);
		return DataSourceBuilder.create()
				.url(fallbackUrl)
				.username(fallbackUsername)
				.password(fallbackPassword)
				.driverClassName("com.mysql.cj.jdbc.Driver")
				.build();
	}

	private boolean isReachable(String host, int port, int timeoutMs) {
		try (Socket socket = new Socket()) {
			socket.connect(new InetSocketAddress(host, port), timeoutMs);
			return true;
		} catch (IOException e) {
			return false;
		}
	}

	private HostPort parseHostPort(String jdbcUrl) {
		if (jdbcUrl == null) return null;
		// Detecta jdbc:mysql://host:port/database o jdbc:mysql://host/database
		Pattern pattern = Pattern.compile("jdbc:mysql://([^:/]+)(?::(\\d+))?/.*");
		Matcher matcher = pattern.matcher(jdbcUrl);
		if (matcher.matches()) {
			String host = matcher.group(1);
			String portStr = matcher.group(2);
			int port = (portStr != null) ? Integer.parseInt(portStr) : 3306;
			return new HostPort(host, port);
		}
		return null;
	}

	private static class HostPort {
		final String host;
		final int port;

		HostPort(String host, int port) {
			this.host = host;
			this.port = port;
		}
	}
}
