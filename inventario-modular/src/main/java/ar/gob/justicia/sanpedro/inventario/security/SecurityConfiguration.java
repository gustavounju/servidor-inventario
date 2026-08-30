package ar.gob.justicia.sanpedro.inventario.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
class SecurityConfiguration {

	@Bean
	SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
		return http
				.authorizeHttpRequests((requests) -> requests
						.requestMatchers("/", "/api/v1/health").permitAll()
						.anyRequest().authenticated())
				.formLogin((form) -> form.disable())
				.httpBasic((basic) -> basic.disable())
				.exceptionHandling((exceptions) -> exceptions
						.authenticationEntryPoint((request, response, authException) ->
								response.sendError(HttpStatus.UNAUTHORIZED.value())))
				.csrf((csrf) -> csrf.disable())
				.build();
	}
}
