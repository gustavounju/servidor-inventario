package ar.gov.justiciajujuy.sanpedro.inventario.config;

import ar.gov.justiciajujuy.sanpedro.inventario.security.ActiveDirectoryUserDetailsContextMapper;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.ldap.core.LdapOperations;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.ldap.authentication.ad.ActiveDirectoryLdapAuthenticationProvider;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.util.StringUtils;

import ar.gov.justiciajujuy.sanpedro.inventario.security.TokenAuthenticationFilter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
public class SecurityConfig {

	@Value("${inventario.security.report-token:}")
	private String reportToken;

	@Bean
	PasswordEncoder passwordEncoder() {
		return new BCryptPasswordEncoder();
	}

	@Bean
	SecurityFilterChain securityFilterChain(
			HttpSecurity http,
			ObjectProvider<AuthenticationProvider> authenticationProviders) throws Exception {
		authenticationProviders.orderedStream().forEach(http::authenticationProvider);

		http
			.addFilterBefore(new TokenAuthenticationFilter(reportToken), UsernamePasswordAuthenticationFilter.class)
			.csrf(csrf -> csrf
				.ignoringRequestMatchers("/api/v1/**", "/submit_inventory")
			)
			.exceptionHandling(exceptions -> exceptions
				.authenticationEntryPoint((request, response, authException) -> {
					String path = request.getRequestURI();
					if (path.startsWith("/api/v1/") || path.equals("/submit_inventory")) {
						response.sendError(401, "Unauthorized");
					} else {
						response.sendRedirect(request.getContextPath() + "/login");
					}
				})
			)
			.authorizeHttpRequests(authorize -> authorize
				.requestMatchers(
					"/", "/login", "/logout",
					"/api/v1/sistema/estado",
					"/css/**", "/js/**", "/images/**", "/scripts/**", "/webjars/**", "/favicon.ico"
				).permitAll()
				.requestMatchers("/submit_inventory").authenticated()
				.anyRequest().authenticated()
			)
			.formLogin(form -> form
				.loginPage("/login")
				.defaultSuccessUrl("/admin", true)
				.permitAll()
			)
			.logout(logout -> logout
				.logoutSuccessUrl("/")
				.permitAll()
			);

		return http.build();
	}

	@Bean
	@ConditionalOnProperty(name = "inventario.ldap.enabled", havingValue = "true")
	LdapOperations activeDirectoryReadOnlyLdapOperations(ActiveDirectoryProperties properties) {
		LdapContextSource contextSource = new LdapContextSource();
		contextSource.setUrl(properties.getUrl());
		contextSource.setBase(properties.getBaseDn());
		if (StringUtils.hasText(properties.getReadOnlyUserDn())) {
			contextSource.setUserDn(properties.getReadOnlyUserDn());
			contextSource.setPassword(properties.getReadOnlyPassword());
		}
		contextSource.afterPropertiesSet();
		return new LdapTemplate(contextSource);
	}

	@Bean
	@Order(30)
	@ConditionalOnProperty(name = "inventario.ldap.enabled", havingValue = "true")
	AuthenticationProvider activeDirectoryAuthenticationProvider(
			ActiveDirectoryProperties properties,
			ActiveDirectoryUserDetailsContextMapper userDetailsContextMapper) {
		ActiveDirectoryLdapAuthenticationProvider provider =
				new ActiveDirectoryLdapAuthenticationProvider(
						properties.getDomain(),
						properties.getUrl(),
						properties.getBaseDn());
		provider.setConvertSubErrorCodesToExceptions(true);
		provider.setUserDetailsContextMapper(userDetailsContextMapper);
		return provider;
	}
}
