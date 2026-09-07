package ar.gov.justiciajujuy.sanpedro.inventario.config;

import java.util.List;
import java.util.Map;

import ar.gov.justiciajujuy.sanpedro.inventario.security.ActiveDirectoryUserDetails;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.util.StringUtils;

/**
 * Configura el login local de desarrollo cuando no hay Active Directory disponible.
 *
 * <p>La clase se activa solo si `inventario.local-auth.enabled=true`. Ademas, sus beans
 * queda disponible cuando la conexion al dominio no existe o se trabaja desde casa.</p>
 */
@Configuration
@ConditionalOnProperty(name = "inventario.local-auth.enabled", havingValue = "true")
public class LocalAuthenticationConfig {

	@Bean
	@Order(20)
	AuthenticationProvider localAuthenticationProvider(
			LocalAuthenticationProperties properties,
			PasswordEncoder passwordEncoder) {
		/*
		 * Este usuario existe solo para estudiar y probar en casa, donde no hay acceso al
		 * dominio real. Reutilizamos ActiveDirectoryUserDetails para que la pantalla vea
		 * una identidad parecida a la que recibe cuando el login viene desde AD. La clave
		 * se codifica al arrancar para evitar ejemplos con password en texto plano dentro
		 * de Spring Security.
		 */
		String configuredUsername = properties.getUsername();
		String encodedPassword = passwordEncoder.encode(properties.getPassword());

		return new AuthenticationProvider() {

			@Override
			public Authentication authenticate(Authentication authentication) {
				String username = String.valueOf(authentication.getPrincipal());
				String password = String.valueOf(authentication.getCredentials());
				if (coincideUsuarioYPassword(username, password)) {
					ActiveDirectoryUserDetails principal = crearPrincipalLocal(encodedPassword, properties);
					return new UsernamePasswordAuthenticationToken(principal, null, principal.getAuthorities());
				}
				throw new BadCredentialsException("Credenciales locales invalidas.");
			}

			@Override
			public boolean supports(Class<?> authentication) {
				return UsernamePasswordAuthenticationToken.class.isAssignableFrom(authentication);
			}

			private boolean coincideUsuarioYPassword(String username, String password) {
				return StringUtils.hasText(username)
						&& configuredUsername.equalsIgnoreCase(username.trim())
						&& passwordEncoder.matches(password, encodedPassword);
			}
		};
	}

	private ActiveDirectoryUserDetails crearPrincipalLocal(
			String encodedPassword,
			LocalAuthenticationProperties properties) {
		/*
		 * Spring Security borra las credenciales del UserDetails autenticado.
		 * Por eso devolvemos una instancia nueva en cada busqueda y conservamos
		 * la clave codificada fuera del objeto que se entrega al framework.
		 */
		return new ActiveDirectoryUserDetails(
				properties.getUsername(),
				encodedPassword,
				List.of(
						new SimpleGrantedAuthority("ROLE_USER"),
						new SimpleGrantedAuthority("ROLE_ADMIN")),
				properties.getDisplayName(),
				properties.getFuero(),
				Map.of(
						"modo", List.of("LOCAL_SIMULADO"),
						"origen", List.of("Windows sin dominio"),
						"descripcion", List.of("Usuario local para desarrollo")));
	}
}
