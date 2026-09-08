package ar.gov.justiciajujuy.sanpedro.inventario.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Propiedades del login local usado solo para desarrollo en Windows/casa.
 *
 * <p>Estas propiedades no representan usuarios reales del dominio. Sirven para levantar
 * la aplicacion cuando Active Directory no esta disponible.</p>
 */
@ConfigurationProperties(prefix = "inventario.local-auth")
public class LocalAuthenticationProperties {

	private boolean enabled;
	private String username = "admin.local";
	private String password;
	private String displayName = "Administrador Local";
	private String fuero = "Desarrollo local";

	public boolean isEnabled() {
		return enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public String getUsername() {
		return username;
	}

	public void setUsername(String username) {
		this.username = username;
	}

	public String getPassword() {
		return password;
	}

	public void setPassword(String password) {
		this.password = password;
	}

	public String getDisplayName() {
		return displayName;
	}

	public void setDisplayName(String displayName) {
		this.displayName = displayName;
	}

	public String getFuero() {
		return fuero;
	}

	public void setFuero(String fuero) {
		this.fuero = fuero;
	}
}
