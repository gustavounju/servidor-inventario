package ar.gov.justiciajujuy.sanpedro.inventario.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.when;

import java.util.List;

import javax.naming.directory.BasicAttribute;
import javax.naming.directory.BasicAttributes;
import javax.naming.directory.SearchControls;

import ar.gov.justiciajujuy.sanpedro.inventario.config.ActiveDirectoryProperties;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.ldap.core.AttributesMapper;
import org.springframework.ldap.core.LdapOperations;

class ActiveDirectoryDomainServiceTests {

	@Test
	void noConsultaLdapCuandoEstaDesactivado() {
		ActiveDirectoryProperties properties = new ActiveDirectoryProperties();
		LdapOperations ldapOperations = mock(LdapOperations.class);
		ActiveDirectoryDomainService service = new ActiveDirectoryDomainService(properties, ldapOperations);

		ActiveDirectoryDomainService.DominioUsuarios resultado = service.buscarUsuarios("gm");

		assertThat(resultado.disponible()).isFalse();
		assertThat(resultado.consultaRealizada()).isTrue();
		assertThat(resultado.query()).isEqualTo("gm");
		assertThat(resultado.mensaje()).isEqualTo("LDAP esta desactivado en este entorno.");
		assertThat(resultado.usuarios()).isEmpty();
	}

	@Test
	void noConsultaLdapSinBusquedaExplicita() {
		ActiveDirectoryProperties properties = new ActiveDirectoryProperties();
		properties.setEnabled(true);
		LdapOperations ldapOperations = mock(LdapOperations.class);
		ActiveDirectoryDomainService service = new ActiveDirectoryDomainService(properties, ldapOperations);

		ActiveDirectoryDomainService.DominioUsuarios resultado = service.listarUsuarios();

		assertThat(resultado.disponible()).isFalse();
		assertThat(resultado.consultaRealizada()).isFalse();
		assertThat(resultado.mensaje()).isEqualTo("Ingrese al menos 2 caracteres para buscar usuarios de dominio.");
		verify(ldapOperations, never()).search(any(String.class), any(String.class), any(SearchControls.class),
				any(AttributesMapper.class));
	}

	@Test
	void informaCuentaLectoraIncompletaSinConsultarLdap() {
		ActiveDirectoryProperties properties = new ActiveDirectoryProperties();
		properties.setEnabled(true);
		properties.setReadOnlyUserDn("CN=lector-inventario,OU=Servicios,DC=podjudsp,DC=local");
		LdapOperations ldapOperations = mock(LdapOperations.class);
		ActiveDirectoryDomainService service = new ActiveDirectoryDomainService(properties, ldapOperations);

		ActiveDirectoryDomainService.DominioUsuarios resultado = service.buscarUsuarios("gmurad");

		assertThat(resultado.disponible()).isFalse();
		assertThat(resultado.consultaRealizada()).isTrue();
		assertThat(resultado.mensaje()).isEqualTo("La cuenta LDAP lectora no tiene clave configurada.");
		verify(ldapOperations, never()).search(any(String.class), any(String.class), any(SearchControls.class),
				any(AttributesMapper.class));
	}

	@Test
	@SuppressWarnings("unchecked")
	void mapeaUsuariosDelDirectorioSinClavesNiAtributosSensibles() throws Exception {
		ActiveDirectoryProperties properties = new ActiveDirectoryProperties();
		properties.setEnabled(true);
		properties.setUserSearchBase("OU=Usuarios");
		properties.setUserSearchFilter("(objectClass=user)");
		LdapOperations ldapOperations = mock(LdapOperations.class);
		BasicAttributes attributes = new BasicAttributes();
		attributes.put(new BasicAttribute("sAMAccountName", "gmurad"));
		attributes.put(new BasicAttribute("displayName", "Gustavo Elias Murad"));
		attributes.put(new BasicAttribute("department", "Informatica"));

		when(ldapOperations.search(
				eq("OU=Usuarios"),
				any(String.class),
				any(SearchControls.class),
				any(AttributesMapper.class)))
			.thenAnswer(invocation -> List.of(
					((AttributesMapper<ActiveDirectoryDomainService.UsuarioDominio>) invocation.getArgument(3))
							.mapFromAttributes(attributes)));

		ActiveDirectoryDomainService service = new ActiveDirectoryDomainService(properties, ldapOperations);

		ActiveDirectoryDomainService.DominioUsuarios resultado = service.buscarUsuarios("gmurad");

		assertThat(resultado.disponible()).isTrue();
		assertThat(resultado.query()).isEqualTo("gmurad");
		assertThat(resultado.usuarios()).containsExactly(
				new ActiveDirectoryDomainService.UsuarioDominio("gmurad", "Gustavo Elias Murad", "Informatica"));
	}

	@Test
	@SuppressWarnings("unchecked")
	void escapaLaBusquedaAntesDeArmarElFiltroLdap() {
		ActiveDirectoryProperties properties = new ActiveDirectoryProperties();
		properties.setEnabled(true);
		LdapOperations ldapOperations = mock(LdapOperations.class);
		when(ldapOperations.search(
				any(String.class),
				any(String.class),
				any(SearchControls.class),
				any(AttributesMapper.class)))
			.thenReturn(List.of());
		ActiveDirectoryDomainService service = new ActiveDirectoryDomainService(properties, ldapOperations);

		service.buscarUsuarios("gm*)(admin");

		ArgumentCaptor<String> filterCaptor = ArgumentCaptor.forClass(String.class);
		verify(ldapOperations).search(any(String.class), filterCaptor.capture(), any(SearchControls.class),
				any(AttributesMapper.class));
		assertThat(filterCaptor.getValue()).contains("gm\\2a\\29\\28admin");
	}

	@Test
	void parseaFueroCorrectamenteDesdeDistinguishedName() {
		ActiveDirectoryDomainService service = new ActiveDirectoryDomainService(new ActiveDirectoryProperties(), (LdapOperations) null);

		String dn = "CN=TTSIVVOC100002,OU=Vocalia 10,OU=Sala IV,OU=Tribunal de Trabajo,OU=EQUIPOS,OU=PODJUDSP,DC=podjudsp,DC=local";
		String fuero = service.parsearFueroDesdeDn(dn);

		assertThat(fuero).isEqualTo("Tribunal de Trabajo - Sala IV - Vocalia 10");
	}

	@Test
	void parseaFueroRetornaNullSiSoloHayContenedoresIgnorados() {
		ActiveDirectoryDomainService service = new ActiveDirectoryDomainService(new ActiveDirectoryProperties(), (LdapOperations) null);

		String dn = "CN=PC-01,OU=EQUIPOS,OU=PODJUDSP,DC=podjudsp,DC=local";
		String fuero = service.parsearFueroDesdeDn(dn);

		assertThat(fuero).isNull();
	}
}
