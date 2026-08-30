package ar.gob.justicia.sanpedro.inventario.login;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
class LocalAuthenticationService {

	private final String configuredUsername;
	private final String configuredPassword;

	LocalAuthenticationService(
			@Value("${inventario.auth.local-admin.username:${BOOTSTRAP_ADMIN_USERNAME:administrador}}") String configuredUsername,
			@Value("${inventario.auth.local-admin.password:${BOOTSTRAP_ADMIN_PASSWORD:}}") String configuredPassword) {
		this.configuredUsername = valueOrDotenv(configuredUsername, "BOOTSTRAP_ADMIN_USERNAME")
				.orElse("administrador")
				.trim()
				.toLowerCase();
		this.configuredPassword = valueOrDotenv(configuredPassword, "BOOTSTRAP_ADMIN_PASSWORD").orElse("");
	}

	AuthenticationResult authenticate(String usernameRaw, String password, String authMode) {
		String username = normalizeUsername(usernameRaw);
		if (username.endsWith("_adm")) {
			return AuthenticationResult.failure("Por seguridad, ingrese con la cuenta comun, no con cuenta _adm.");
		}

		if ("domain".equalsIgnoreCase(authMode)) {
			return AuthenticationResult.failure("La autenticacion de dominio queda preparada, pero se conecta cuando tengamos AD disponible en la red del trabajo.");
		}

		if (configuredPassword.isBlank()) {
			return AuthenticationResult.failure("Falta configurar BOOTSTRAP_ADMIN_PASSWORD en el entorno o en .env.");
		}

		if (!configuredUsername.equals(username) || !constantTimeEquals(configuredPassword, password)) {
			return AuthenticationResult.failure("Usuario o clave incorrectos.");
		}

		return AuthenticationResult.success(new AuthenticatedUser(configuredUsername, "Administrador", "administrador", true));
	}

	private String normalizeUsername(String value) {
		String normalized = (value == null ? "" : value).trim().toLowerCase();
		if (normalized.contains("\\")) {
			normalized = normalized.substring(normalized.lastIndexOf('\\') + 1);
		}
		if (normalized.contains("@")) {
			normalized = normalized.substring(0, normalized.indexOf('@'));
		}
		return normalized;
	}

	private boolean constantTimeEquals(String expected, String actual) {
		byte[] left = expected.getBytes(StandardCharsets.UTF_8);
		byte[] right = (actual == null ? "" : actual).getBytes(StandardCharsets.UTF_8);
		int diff = left.length ^ right.length;
		for (int i = 0; i < Math.max(left.length, right.length); i++) {
			byte a = i < left.length ? left[i] : 0;
			byte b = i < right.length ? right[i] : 0;
			diff |= a ^ b;
		}
		return diff == 0;
	}

	private Optional<String> valueOrDotenv(String configuredValue, String key) {
		if (configuredValue != null && !configuredValue.isBlank()) {
			return Optional.of(configuredValue);
		}
		return dotenvValue(key);
	}

	private Optional<String> dotenvValue(String key) {
		for (Path candidate : dotenvCandidates()) {
			if (!Files.isRegularFile(candidate)) {
				continue;
			}
			try {
				for (String line : Files.readAllLines(candidate, StandardCharsets.UTF_8)) {
					String trimmed = line.trim();
					if (trimmed.startsWith("#") || !trimmed.startsWith(key + "=")) {
						continue;
					}
					return Optional.of(unquote(trimmed.substring(key.length() + 1).trim()));
				}
			}
			catch (IOException ignored) {
				return Optional.empty();
			}
		}
		return Optional.empty();
	}

	private Path[] dotenvCandidates() {
		Path current = Path.of("").toAbsolutePath();
		return new Path[] {
				current.resolve(".env"),
				current.getParent() == null ? current.resolve(".env") : current.getParent().resolve(".env")
		};
	}

	private String unquote(String value) {
		if ((value.startsWith("\"") && value.endsWith("\"")) || (value.startsWith("'") && value.endsWith("'"))) {
			return value.substring(1, value.length() - 1);
		}
		return value;
	}
}
