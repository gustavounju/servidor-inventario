package ar.gov.justiciajujuy.sanpedro.inventario.security;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;

import ar.gov.justiciajujuy.sanpedro.inventario.config.NetworkAccessProperties;
import jakarta.servlet.ServletException;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockFilterChain;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

class LanOnlyAccessFilterTests {

	@Test
	void allowsPrivateLanAddress() throws ServletException, IOException {
		LanOnlyAccessFilter filter = new LanOnlyAccessFilter(new NetworkAccessProperties());
		MockHttpServletRequest request = new MockHttpServletRequest("GET", "/login");
		MockHttpServletResponse response = new MockHttpServletResponse();
		MockFilterChain chain = new MockFilterChain();
		request.setRemoteAddr("10.15.2.10");

		filter.doFilter(request, response, chain);

		assertThat(response.getStatus()).isEqualTo(200);
	}

	@Test
	void blocksPublicAddress() throws ServletException, IOException {
		LanOnlyAccessFilter filter = new LanOnlyAccessFilter(new NetworkAccessProperties());
		MockHttpServletRequest request = new MockHttpServletRequest("GET", "/login");
		MockHttpServletResponse response = new MockHttpServletResponse();
		request.setRemoteAddr("8.8.8.8");

		filter.doFilter(request, response, new MockFilterChain());

		assertThat(response.getStatus()).isEqualTo(403);
	}

	@Test
	void honorsConfiguredAllowedCidrsForPrivateAddresses() throws ServletException, IOException {
		NetworkAccessProperties properties = new NetworkAccessProperties();
		properties.setAllowedCidrs(java.util.List.of("10.15.0.0/16"));
		LanOnlyAccessFilter filter = new LanOnlyAccessFilter(properties);
		MockHttpServletRequest request = new MockHttpServletRequest("GET", "/login");
		MockHttpServletResponse response = new MockHttpServletResponse();
		request.setRemoteAddr("192.168.1.20");

		filter.doFilter(request, response, new MockFilterChain());

		assertThat(response.getStatus()).isEqualTo(403);
	}

	@Test
	void usesForwardedAddressOnlyWhenProxyIsLocal() throws ServletException, IOException {
		LanOnlyAccessFilter filter = new LanOnlyAccessFilter(new NetworkAccessProperties());
		MockHttpServletRequest request = new MockHttpServletRequest("GET", "/login");
		MockHttpServletResponse response = new MockHttpServletResponse();
		request.setRemoteAddr("127.0.0.1");
		request.addHeader("X-Forwarded-For", "203.0.113.20");

		filter.doFilter(request, response, new MockFilterChain());

		assertThat(response.getStatus()).isEqualTo(403);
	}
}
