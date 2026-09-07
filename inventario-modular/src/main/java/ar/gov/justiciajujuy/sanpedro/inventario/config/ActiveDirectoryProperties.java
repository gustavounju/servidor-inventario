package ar.gov.justiciajujuy.sanpedro.inventario.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "inventario.ldap")
public class ActiveDirectoryProperties {

	private boolean enabled;
	private String url = "ldap://SERVIDOR_AD:389";
	private String domain = "DOMINIO";
	private String baseDn = "DC=ejemplo,DC=local";
	private String displayNameAttribute = "displayName";
	private String fueroAttribute = "department";
	private String readOnlyUserDn = "";
	private String readOnlyPassword = "";
	private String userSearchBase = "";
	private String userSearchFilter = "(&(objectClass=user)(!(objectClass=computer)))";
	private int userSearchLimit = 50;

	public boolean isEnabled() {
		return enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public String getUrl() {
		return url;
	}

	public void setUrl(String url) {
		this.url = url;
	}

	public String getDomain() {
		return domain;
	}

	public void setDomain(String domain) {
		this.domain = domain;
	}

	public String getBaseDn() {
		return baseDn;
	}

	public void setBaseDn(String baseDn) {
		this.baseDn = baseDn;
	}

	public String getDisplayNameAttribute() {
		return displayNameAttribute;
	}

	public void setDisplayNameAttribute(String displayNameAttribute) {
		this.displayNameAttribute = displayNameAttribute;
	}

	public String getFueroAttribute() {
		return fueroAttribute;
	}

	public void setFueroAttribute(String fueroAttribute) {
		this.fueroAttribute = fueroAttribute;
	}

	public String getReadOnlyUserDn() {
		return readOnlyUserDn;
	}

	public void setReadOnlyUserDn(String readOnlyUserDn) {
		this.readOnlyUserDn = readOnlyUserDn;
	}

	public String getReadOnlyPassword() {
		return readOnlyPassword;
	}

	public void setReadOnlyPassword(String readOnlyPassword) {
		this.readOnlyPassword = readOnlyPassword;
	}

	public String getUserSearchBase() {
		return userSearchBase;
	}

	public void setUserSearchBase(String userSearchBase) {
		this.userSearchBase = userSearchBase;
	}

	public String getUserSearchFilter() {
		return userSearchFilter;
	}

	public void setUserSearchFilter(String userSearchFilter) {
		this.userSearchFilter = userSearchFilter;
	}

	public int getUserSearchLimit() {
		return userSearchLimit;
	}

	public void setUserSearchLimit(int userSearchLimit) {
		this.userSearchLimit = userSearchLimit;
	}
}
