package ar.gov.justiciajujuy.sanpedro.inventario.config;

import java.util.Map;
import java.util.Optional;

import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class SiteAvailabilityService {

	private static final String KEY_TEMPORARILY_INACTIVE = "sitio_temporalmente_inactivo";
	private static final String KEY_MESSAGE = "sitio_mensaje_inactivo";
	private static final String KEY_ALLOWED_USERNAME = "sitio_usuario_acceso_emergencia";
	private static final String DEFAULT_ALLOWED_USERNAME = "gmurad";
	private static final String DEFAULT_MESSAGE = "El sistema esta temporalmente inactivo por tareas de mantenimiento.";

	private final JdbcTemplate jdbcTemplate;

	public SiteAvailabilityService(JdbcTemplate jdbcTemplate) {
		this.jdbcTemplate = jdbcTemplate;
	}

	@Transactional(readOnly = true)
	public SiteAvailability current() {
		Map<String, String> values = readValues();
		boolean temporarilyInactive = Boolean.parseBoolean(
				values.getOrDefault(KEY_TEMPORARILY_INACTIVE, "false"));
		String allowedUsername = normalize(values.get(KEY_ALLOWED_USERNAME))
				.orElse(DEFAULT_ALLOWED_USERNAME);
		String message = normalize(values.get(KEY_MESSAGE))
				.orElse(DEFAULT_MESSAGE);
		return new SiteAvailability(temporarilyInactive, message, allowedUsername);
	}

	@Transactional
	public void update(boolean temporarilyInactive, String message, String allowedUsername) {
		upsert(KEY_TEMPORARILY_INACTIVE, Boolean.toString(temporarilyInactive));
		upsert(KEY_MESSAGE, normalize(message).orElse(DEFAULT_MESSAGE));
		upsert(KEY_ALLOWED_USERNAME, normalize(allowedUsername).orElse(DEFAULT_ALLOWED_USERNAME));
	}

	public boolean canAccessWhileInactive(String username) {
		SiteAvailability availability = current();
		return !availability.temporarilyInactive()
				|| availability.allowedUsername().equalsIgnoreCase(normalize(username).orElse(""));
	}

	private Map<String, String> readValues() {
		try {
			return jdbcTemplate.query(
					"""
					SELECT clave, valor
					FROM configuraciones_sistema
					WHERE clave IN (?, ?, ?)
					""",
					rs -> {
						Map<String, String> values = new java.util.HashMap<>();
						while (rs.next()) {
							values.put(rs.getString("clave"), rs.getString("valor"));
						}
						return values;
					},
					KEY_TEMPORARILY_INACTIVE,
					KEY_MESSAGE,
					KEY_ALLOWED_USERNAME);
		} catch (DataAccessException ex) {
			return Map.of();
		}
	}

	private void upsert(String key, String value) {
		int updated = jdbcTemplate.update(
				"""
				UPDATE configuraciones_sistema
				SET valor = ?, actualizado_en = CURRENT_TIMESTAMP
				WHERE clave = ?
				""",
				value,
				key);
		if (updated == 0) {
			jdbcTemplate.update(
					"""
					INSERT INTO configuraciones_sistema (clave, valor)
					VALUES (?, ?)
					""",
					key,
					value);
		}
	}

	private Optional<String> normalize(String value) {
		if (!StringUtils.hasText(value)) {
			return Optional.empty();
		}
		return Optional.of(value.trim());
	}

	public record SiteAvailability(
			boolean temporarilyInactive,
			String message,
			String allowedUsername) {
	}
}
