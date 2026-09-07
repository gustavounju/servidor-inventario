package ar.gov.justiciajujuy.sanpedro.inventario.config;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.sql.DataSource;

import org.springframework.core.env.Environment;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class RuntimeModeService {

	private static final Pattern JDBC_MYSQL = Pattern.compile("jdbc:mysql://([^:/]+)(?::(\\d+))?/([^?;]+).*");
	private static final Pattern LDAP = Pattern.compile("ldaps?://([^:/]+)(?::(\\d+))?.*");

	private final DataSource dataSource;
	private final Environment environment;
	private final ActiveDirectoryProperties activeDirectoryProperties;

	public RuntimeModeService(
			DataSource dataSource,
			Environment environment,
			ActiveDirectoryProperties activeDirectoryProperties) {
		this.dataSource = dataSource;
		this.environment = environment;
		this.activeDirectoryProperties = activeDirectoryProperties;
	}

	public RuntimeMode current() {
		DatabaseInfo databaseInfo = databaseInfo();
		boolean ldapConfigured = activeDirectoryProperties.isEnabled();
		boolean ldapReachable = ldapConfigured && ldapReachable();
		String workMode = databaseInfo.remote() && ldapReachable ? "TRABAJO" : "LOCAL";
		String authMode = ldapReachable ? "Active Directory + autorizacion local" : "Usuarios locales";
		String message = databaseInfo.remote() && ldapReachable
				? "Conectado a red de trabajo: usuarios de dominio y MySQL remoto."
				: "Modo local/fallback: se usan usuarios locales y base local disponible.";

		return new RuntimeMode(
				activeProfile(),
				workMode,
				databaseInfo.mode(),
				databaseInfo.safeUrl(),
				ldapConfigured,
				ldapReachable,
				authMode,
				message);
	}

	private String activeProfile() {
		String[] profiles = environment.getActiveProfiles();
		return profiles.length == 0 ? "default" : String.join(",", profiles);
	}

	private DatabaseInfo databaseInfo() {
		try (Connection connection = dataSource.getConnection()) {
			String url = connection.getMetaData().getURL();
			String product = connection.getMetaData().getDatabaseProductName();
			Matcher matcher = JDBC_MYSQL.matcher(url == null ? "" : url);
			boolean remote = matcher.matches()
					&& !"127.0.0.1".equals(matcher.group(1))
					&& !"localhost".equalsIgnoreCase(matcher.group(1));
			String mode = remote ? "MySQL remoto" : product + " local";
			return new DatabaseInfo(mode, safeJdbcUrl(url), remote);
		} catch (SQLException ex) {
			return new DatabaseInfo("No disponible", "No disponible", false);
		}
	}

	private boolean ldapReachable() {
		Matcher matcher = LDAP.matcher(activeDirectoryProperties.getUrl());
		if (!matcher.matches() || !StringUtils.hasText(matcher.group(1))) {
			return false;
		}
		int port = matcher.group(2) == null
				? (activeDirectoryProperties.getUrl().startsWith("ldaps://") ? 636 : 389)
				: Integer.parseInt(matcher.group(2));
		try (Socket socket = new Socket()) {
			socket.connect(new InetSocketAddress(matcher.group(1), port), 1200);
			return true;
		} catch (IOException ex) {
			return false;
		}
	}

	private String safeJdbcUrl(String url) {
		if (!StringUtils.hasText(url)) {
			return "No disponible";
		}
		Matcher matcher = JDBC_MYSQL.matcher(url);
		if (matcher.matches()) {
			return "mysql://" + matcher.group(1) + ":" + (matcher.group(2) == null ? "3306" : matcher.group(2))
					+ "/" + matcher.group(3);
		}
		if (url.startsWith("jdbc:h2:file:")) {
			return "h2:file:" + url.substring("jdbc:h2:file:".length()).split(";")[0];
		}
		if (url.startsWith("jdbc:h2:mem:")) {
			return "h2:mem";
		}
		return "Configurada";
	}

	private record DatabaseInfo(String mode, String safeUrl, boolean remote) {
	}

	public record RuntimeMode(
			String perfil,
			String modoTrabajo,
			String baseDatos,
			String baseDatosUrl,
			boolean activeDirectoryConfigurado,
			boolean activeDirectoryDisponible,
			String autenticacion,
			String mensaje) {
	}
}
