package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.config.RuntimeModeService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/sistema")
public class SystemStatusController {

	private final String applicationName;
	private final String version;
	private final RuntimeModeService runtimeModeService;

	public SystemStatusController(
			@Value("${spring.application.name}") String applicationName,
			@Value("${inventario.version}") String version,
			RuntimeModeService runtimeModeService) {
		this.applicationName = applicationName;
		this.version = version;
		this.runtimeModeService = runtimeModeService;
	}

	@GetMapping("/estado")
	public SystemStatusResponse status() {
		return new SystemStatusResponse("OPERATIVO", applicationName, version);
	}

	@GetMapping("/runtime")
	public RuntimeStatusResponse runtime() {
		return new RuntimeStatusResponse("OPERATIVO", applicationName, version, runtimeModeService.current());
	}

	public record SystemStatusResponse(
			String estado,
			String aplicacion,
			String version) {
	}

	public record RuntimeStatusResponse(
			String estado,
			String aplicacion,
			String version,
			RuntimeModeService.RuntimeMode modo) {
	}
}
