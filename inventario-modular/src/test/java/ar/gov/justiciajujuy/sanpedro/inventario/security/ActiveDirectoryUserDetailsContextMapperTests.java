package ar.gov.justiciajujuy.sanpedro.inventario.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatExceptionOfType;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.config.ActiveDirectoryProperties;
import javax.naming.directory.BasicAttribute;
import javax.naming.directory.BasicAttributes;
import org.junit.jupiter.api.Test;
import org.springframework.ldap.core.DirContextAdapter;
import org.springframework.ldap.core.DirContextOperations;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.User;

class ActiveDirectoryUserDetailsContextMapperTests {

	@Test
	void mapsDisplayNameAndFueroFromConfiguredActiveDirectoryAttributes() {
		ActiveDirectoryProperties properties = new ActiveDirectoryProperties();
		DirContextOperations context = mock(DirContextOperations.class);
		when(context.getStringAttribute("displayName")).thenReturn("Gustavo Elias Murad");
		when(context.getStringAttribute("department")).thenReturn("Penal");
		BasicAttributes attributes = new BasicAttributes();
		attributes.put(new BasicAttribute("displayName", "Gustavo Elias Murad"));
		attributes.put(new BasicAttribute("department", "Penal"));
		attributes.put(new BasicAttribute("mail", "gmurad@podjudsp.local"));
		attributes.put(new BasicAttribute("pwdLastSet", "133000000000000000"));
		when(context.getAttributes()).thenReturn(attributes);

		ActiveDirectoryUserDetailsContextMapper mapper =
				new ActiveDirectoryUserDetailsContextMapper(properties);

		ActiveDirectoryUserDetails userDetails = (ActiveDirectoryUserDetails) mapper.mapUserFromContext(
				context,
				"gmurad",
				List.of(new SimpleGrantedAuthority("ROLE_USER")));

		assertThat(userDetails.getUsername()).isEqualTo("gmurad");
		assertThat(userDetails.getDisplayName()).isEqualTo("Gustavo Elias Murad");
		assertThat(userDetails.getFuero()).isEqualTo("Penal");
		assertThat(userDetails.getAttributes())
			.containsEntry("displayName", List.of("Gustavo Elias Murad"))
			.containsEntry("department", List.of("Penal"))
			.containsEntry("mail", List.of("gmurad@podjudsp.local"))
			.doesNotContainKey("pwdLastSet");
	}

	@Test
	void usesSafeFallbacksWhenActiveDirectoryAttributesAreEmpty() {
		ActiveDirectoryProperties properties = new ActiveDirectoryProperties();
		DirContextOperations context = mock(DirContextOperations.class);
		when(context.getAttributes()).thenReturn(new BasicAttributes());

		ActiveDirectoryUserDetailsContextMapper mapper =
				new ActiveDirectoryUserDetailsContextMapper(properties);

		ActiveDirectoryUserDetails userDetails = (ActiveDirectoryUserDetails) mapper.mapUserFromContext(
				context,
				"gmurad",
				List.of(new SimpleGrantedAuthority("ROLE_USER")));

		assertThat(userDetails.getDisplayName()).isEqualTo("gmurad");
		assertThat(userDetails.getFuero()).isEqualTo("Sin fuero informado");
	}

	@Test
	void refusesToWriteUserDataBackToActiveDirectory() {
		ActiveDirectoryProperties properties = new ActiveDirectoryProperties();
		ActiveDirectoryUserDetailsContextMapper mapper =
				new ActiveDirectoryUserDetailsContextMapper(properties);

		assertThatExceptionOfType(UnsupportedOperationException.class)
			.isThrownBy(() -> mapper.mapUserToContext(
					User.withUsername("gmurad").password("unused").roles("USER").build(),
					new DirContextAdapter()))
			.withMessage("Inventario Modular solo lee usuarios desde Active Directory.");
	}
}
