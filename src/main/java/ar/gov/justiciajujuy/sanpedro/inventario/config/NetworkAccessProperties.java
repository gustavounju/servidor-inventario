package ar.gov.justiciajujuy.sanpedro.inventario.config;

import java.util.ArrayList;
import java.util.List;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "inventario.security.network")
public class NetworkAccessProperties {

	private boolean lanOnly = true;
	private List<String> allowedCidrs = new ArrayList<>(List.of(
			"127.0.0.0/8",
			"10.0.0.0/8",
			"172.16.0.0/12",
			"192.168.0.0/16",
			"::1/128"));
	private boolean trustForwardedHeaders = true;

	public boolean isLanOnly() {
		return lanOnly;
	}

	public void setLanOnly(boolean lanOnly) {
		this.lanOnly = lanOnly;
	}

	public List<String> getAllowedCidrs() {
		return allowedCidrs;
	}

	public void setAllowedCidrs(List<String> allowedCidrs) {
		this.allowedCidrs = allowedCidrs;
	}

	public boolean isTrustForwardedHeaders() {
		return trustForwardedHeaders;
	}

	public void setTrustForwardedHeaders(boolean trustForwardedHeaders) {
		this.trustForwardedHeaders = trustForwardedHeaders;
	}
}
