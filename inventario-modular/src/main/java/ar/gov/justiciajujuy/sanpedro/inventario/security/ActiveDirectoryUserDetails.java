package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.util.Collection;
import java.util.List;
import java.util.Map;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.User;

public class ActiveDirectoryUserDetails extends User {

	private final String displayName;
	private final String fuero;
	private final Map<String, List<String>> attributes;

	public ActiveDirectoryUserDetails(
			String username,
			String password,
			Collection<? extends GrantedAuthority> authorities,
			String displayName,
			String fuero,
			Map<String, List<String>> attributes) {
		super(username, password, authorities);
		this.displayName = displayName;
		this.fuero = fuero;
		this.attributes = Map.copyOf(attributes);
	}

	public String getDisplayName() {
		return displayName;
	}

	public String getFuero() {
		return fuero;
	}

	public Map<String, List<String>> getAttributes() {
		return attributes;
	}
}
