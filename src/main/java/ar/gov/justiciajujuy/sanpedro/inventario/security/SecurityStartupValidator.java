package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.net.URI;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import ar.gov.justiciajujuy.sanpedro.inventario.config.ActiveDirectoryProperties;
import ar.gov.justiciajujuy.sanpedro.inventario.config.LocalAuthenticationProperties;
import ar.gov.justiciajujuy.sanpedro.inventario.config.NetworkAccessProperties;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

@Component
@Profile("!test")
public class SecurityStartupValidator implements ApplicationRunner {

	private static final Pattern JDBC_MYSQL = Pattern.compile("jdbc:mysql://([^:/?]+)(?::\\d+)?/.*");

	private final ActiveDirectoryProperties activeDirectoryProperties;
	private final LocalAuthenticationProperties localAuthenticationProperties;
	private final NetworkAccessProperties networkAccessProperties;
	private final boolean localDbAuthenticationEnabled;
	private final String primaryDataSourceUrl;
	private final String fallbackDataSourceUrl;

	public SecurityStartupValidator(
			ActiveDirectoryProperties activeDirectoryProperties,
			LocalAuthenticationProperties localAuthenticationProperties,
			NetworkAccessProperties networkAccessProperties,
			@Value("${inventario.local-db-auth.enabled:false}") boolean localDbAuthenticationEnabled,
			@Value("${inventario.datasource.primary.url:}") String primaryDataSourceUrl,
			@Value("${inventario.datasource.fallback.url:}") String fallbackDataSourceUrl) {
		this.activeDirectoryProperties = activeDirectoryProperties;
		this.localAuthenticationProperties = localAuthenticationProperties;
		this.networkAccessProperties = networkAccessProperties;
		this.localDbAuthenticationEnabled = localDbAuthenticationEnabled;
		this.primaryDataSourceUrl = primaryDataSourceUrl;
		this.fallbackDataSourceUrl = fallbackDataSourceUrl;
	}

	@Override
	public void run(ApplicationArguments args) {
		if (!activeDirectoryProperties.isEnabled()
				&& !localAuthenticationProperties.isEnabled()
				&& !localDbAuthenticationEnabled) {
			throw new IllegalStateException(
					"Debe configurar al menos un metodo de autenticacion: Active Directory, usuario local explicito o usuarios locales de base.");
		}

		if (localAuthenticationProperties.isEnabled()) {
			requireText(localAuthenticationProperties.getUsername(), "inventario.local-auth.username");
			requireText(localAuthenticationProperties.getPassword(), "inventario.local-auth.password");
		}

		if (networkAccessProperties.isLanOnly()) {
			NetworkAddressPolicy addressPolicy = new NetworkAddressPolicy(networkAccessProperties.getAllowedCidrs());
			requireLanHost(extractJdbcMysqlHost(primaryDataSourceUrl), "inventario.datasource.primary.url", addressPolicy);
			requireLanHost(extractJdbcMysqlHost(fallbackDataSourceUrl), "inventario.datasource.fallback.url", addressPolicy);
			if (activeDirectoryProperties.isEnabled()) {
				requireLanHost(extractUriHost(activeDirectoryProperties.getUrl()), "inventario.ldap.url", addressPolicy);
			}
		}
	}

	private void requireText(String value, String propertyName) {
		if (!StringUtils.hasText(value)) {
			throw new IllegalStateException("Falta configurar " + propertyName + ".");
		}
	}

	private void requireLanHost(String host, String propertyName, NetworkAddressPolicy addressPolicy) {
		if (StringUtils.hasText(host) && !addressPolicy.isAllowed(host)) {
			throw new IllegalStateException(propertyName + " apunta fuera de la LAN permitida: " + host);
		}
	}

	private String extractJdbcMysqlHost(String jdbcUrl) {
		if (!StringUtils.hasText(jdbcUrl)) {
			return "";
		}
		Matcher matcher = JDBC_MYSQL.matcher(jdbcUrl);
		return matcher.matches() ? matcher.group(1) : "";
	}

	private String extractUriHost(String url) {
		if (!StringUtils.hasText(url)) {
			return "";
		}
		return URI.create(url).getHost();
	}
}
