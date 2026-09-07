package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.naming.NamingEnumeration;
import javax.naming.NamingException;
import javax.naming.directory.Attribute;
import javax.naming.directory.Attributes;

import ar.gov.justiciajujuy.sanpedro.inventario.config.ActiveDirectoryProperties;
import org.springframework.ldap.core.DirContextAdapter;
import org.springframework.ldap.core.DirContextOperations;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.ldap.userdetails.UserDetailsContextMapper;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

@Component
public class ActiveDirectoryUserDetailsContextMapper implements UserDetailsContextMapper {

	private static final Set<String> HIDDEN_ATTRIBUTE_NAMES = Set.of(
			"userpassword",
			"unicodepwd",
			"pwdlastset",
			"accountexpires",
			"badpasswordtime",
			"badpwdcount",
			"lockouttime",
			"lastlogon",
			"lastlogontimestamp");

	private final ActiveDirectoryProperties properties;

	public ActiveDirectoryUserDetailsContextMapper(ActiveDirectoryProperties properties) {
		this.properties = properties;
	}

	@Override
	public UserDetails mapUserFromContext(
				DirContextOperations ctx,
				String username,
				Collection<? extends GrantedAuthority> authorities) {
		String displayName = firstText(ctx, properties.getDisplayNameAttribute(), username);
		String fuero = firstText(ctx, properties.getFueroAttribute(), "Sin fuero informado");
		return new ActiveDirectoryUserDetails(username, "", authorities, displayName, fuero, readableAttributes(ctx));
	}

	@Override
	public void mapUserToContext(UserDetails user, DirContextAdapter ctx) {
		throw new UnsupportedOperationException("Inventario Modular solo lee usuarios desde Active Directory.");
	}

	private String firstText(DirContextOperations ctx, String attributeName, String fallback) {
		if (!StringUtils.hasText(attributeName)) {
			return fallback;
		}
		String value = ctx.getStringAttribute(attributeName);
		return StringUtils.hasText(value) ? value : fallback;
	}

	private Map<String, List<String>> readableAttributes(DirContextOperations ctx) {
		Map<String, List<String>> attributes = new LinkedHashMap<>();
		try {
			Attributes contextAttributes = ctx.getAttributes();
			NamingEnumeration<? extends Attribute> allAttributes = contextAttributes.getAll();
			while (allAttributes.hasMore()) {
				Attribute attribute = allAttributes.next();
				String attributeId = attribute.getID();
				if (!StringUtils.hasText(attributeId) || HIDDEN_ATTRIBUTE_NAMES.contains(attributeId.toLowerCase())) {
					continue;
				}
				List<String> values = attributeValues(attribute);
				if (!values.isEmpty()) {
					attributes.put(attributeId, values);
				}
			}
		}
		catch (NamingException ignored) {
			return Map.of();
		}
		return attributes;
	}

	private List<String> attributeValues(Attribute attribute) throws NamingException {
		List<String> values = new java.util.ArrayList<>();
		NamingEnumeration<?> allValues = attribute.getAll();
		while (allValues.hasMore()) {
			Object rawValue = allValues.next();
			if (rawValue instanceof byte[]) {
				values.add("[valor binario]");
				continue;
			}
			String value = String.valueOf(rawValue).trim();
			if (StringUtils.hasText(value)) {
				values.add(value);
			}
		}
		return values;
	}
}
