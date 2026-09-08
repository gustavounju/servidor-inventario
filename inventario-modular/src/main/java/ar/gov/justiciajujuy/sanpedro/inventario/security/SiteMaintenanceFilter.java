package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.io.IOException;

import ar.gov.justiciajujuy.sanpedro.inventario.config.SiteAvailabilityService;
import ar.gov.justiciajujuy.sanpedro.inventario.config.SiteAvailabilityService.SiteAvailability;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpMethod;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

public class SiteMaintenanceFilter extends OncePerRequestFilter {

	private final SiteAvailabilityService siteAvailabilityService;

	public SiteMaintenanceFilter(SiteAvailabilityService siteAvailabilityService) {
		this.siteAvailabilityService = siteAvailabilityService;
	}

	@Override
	protected void doFilterInternal(
			HttpServletRequest request,
			HttpServletResponse response,
			FilterChain filterChain) throws ServletException, IOException {
		SiteAvailability availability = siteAvailabilityService.current();
		if (!availability.temporarilyInactive() || isAlwaysAllowed(request)) {
			filterChain.doFilter(request, response);
			return;
		}

		if (isAllowedLoginAttempt(request, availability) || isAllowedAuthenticatedUser(availability)) {
			filterChain.doFilter(request, response);
			return;
		}

		HttpSession session = request.getSession(false);
		if (session != null) {
			session.invalidate();
		}
		SecurityContextHolder.clearContext();
		if (isApiRequest(request)) {
			response.sendError(HttpServletResponse.SC_SERVICE_UNAVAILABLE, "Sitio temporalmente inactivo.");
			return;
		}
		response.sendRedirect(request.getContextPath() + "/login?inactive");
	}

	private boolean isAlwaysAllowed(HttpServletRequest request) {
		String path = path(request);
		return (path.equals("/login") && HttpMethod.GET.matches(request.getMethod()))
				|| path.equals("/logout")
				|| path.equals("/api/v1/sistema/estado")
				|| path.startsWith("/css/")
				|| path.startsWith("/js/")
				|| path.startsWith("/images/")
				|| path.startsWith("/webjars/")
				|| path.equals("/favicon.ico");
	}

	private boolean isAllowedLoginAttempt(HttpServletRequest request, SiteAvailability availability) {
		if (!path(request).equals("/login") || !HttpMethod.POST.matches(request.getMethod())) {
			return false;
		}
		String username = request.getParameter("username");
		return availability.allowedUsername().equalsIgnoreCase(username != null ? username.trim() : "");
	}

	private boolean isAllowedAuthenticatedUser(SiteAvailability availability) {
		Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
		return authentication != null
				&& authentication.isAuthenticated()
				&& StringUtils.hasText(authentication.getName())
				&& availability.allowedUsername().equalsIgnoreCase(authentication.getName().trim());
	}

	private boolean isApiRequest(HttpServletRequest request) {
		String path = path(request);
		return path.startsWith("/api/") || path.equals("/submit_inventory");
	}

	private String path(HttpServletRequest request) {
		return request.getRequestURI().substring(request.getContextPath().length());
	}
}
