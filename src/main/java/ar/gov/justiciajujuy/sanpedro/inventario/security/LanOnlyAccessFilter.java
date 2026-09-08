package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.io.IOException;
import ar.gov.justiciajujuy.sanpedro.inventario.config.NetworkAccessProperties;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.filter.OncePerRequestFilter;

public class LanOnlyAccessFilter extends OncePerRequestFilter {

	private final NetworkAccessProperties properties;
	private final NetworkAddressPolicy addressPolicy;

	public LanOnlyAccessFilter(NetworkAccessProperties properties) {
		this.properties = properties;
		this.addressPolicy = new NetworkAddressPolicy(properties.getAllowedCidrs());
	}

	@Override
	protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
			throws ServletException, IOException {
		if (!properties.isLanOnly()) {
			filterChain.doFilter(request, response);
			return;
		}

		String clientIp = resolveClientIp(request);
		if (addressPolicy.isAllowed(clientIp)) {
			filterChain.doFilter(request, response);
			return;
		}

		response.sendError(HttpServletResponse.SC_FORBIDDEN, "Acceso permitido solo desde la red institucional.");
	}

	private String resolveClientIp(HttpServletRequest request) {
		String remoteAddress = request.getRemoteAddr();
		if (!properties.isTrustForwardedHeaders() || !addressPolicy.isLoopback(remoteAddress)) {
			return remoteAddress;
		}
		String forwardedFor = request.getHeader("X-Forwarded-For");
		if (forwardedFor == null || forwardedFor.isBlank()) {
			return remoteAddress;
		}
		return forwardedFor.split(",")[0].trim();
	}

}
