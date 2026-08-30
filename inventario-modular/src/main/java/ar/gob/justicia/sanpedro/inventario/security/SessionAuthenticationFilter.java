package ar.gob.justicia.sanpedro.inventario.security;

import java.io.IOException;
import java.util.List;

import ar.gob.justicia.sanpedro.inventario.login.AuthenticatedUser;
import ar.gob.justicia.sanpedro.inventario.login.LoginController;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
class SessionAuthenticationFilter extends OncePerRequestFilter {

	@Override
	protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
			throws ServletException, IOException {
		Object user = request.getSession(false) == null
				? null
				: request.getSession(false).getAttribute(LoginController.AUTH_SESSION_KEY);
		if (user instanceof AuthenticatedUser authenticatedUser) {
			UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
					authenticatedUser.username(),
					null,
					List.of(new SimpleGrantedAuthority("ROLE_ADMIN")));
			SecurityContextHolder.getContext().setAuthentication(authentication);
		}

		filterChain.doFilter(request, response);
	}
}
