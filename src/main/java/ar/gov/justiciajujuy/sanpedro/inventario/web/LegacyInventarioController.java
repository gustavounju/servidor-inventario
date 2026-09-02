package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.EquipoDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.ReporteInventarioCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Map;

@RestController
public class LegacyInventarioController {

	private static final String MODULO_EQUIPOS = "EQUIPOS";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final EquipoService equipoService;
	private final ComponenteService componenteService;

	public LegacyInventarioController(AuthorizationService authorizationService, EquipoService equipoService, ComponenteService componenteService) {
		this.authorizationService = authorizationService;
		this.equipoService = equipoService;
		this.componenteService = componenteService;
	}

	@PostMapping("/submit_inventory")
	@ResponseStatus(HttpStatus.OK)
	public Map<String, String> submitLegacyInventory(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestBody Map<String, Object> payload) {

		if (!authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, PERMISO_EDITAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para reportar equipos.");
		}

		String nombre = (String) payload.get("PC_Nombre");
		if (nombre == null || nombre.trim().isEmpty()) {
			throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Falta PC_Nombre en el payload");
		}

		String ultimoUsuario = (String) payload.get("Usuario_Actual");

		Map<String, Object> sistema = (Map<String, Object>) payload.get("Sistema");
		String osName = null;
		String procesador = null;
		Integer ramMb = null;
		if (sistema != null) {
			osName = (String) sistema.get("OsName");
			procesador = (String) sistema.get("Procesador");
			Object ramObj = sistema.get("RAM (GB)");
			if (ramObj instanceof Number) {
				double ramGb = ((Number) ramObj).doubleValue();
				ramMb = (int) Math.round(ramGb * 1024);
			}
		}

		List<Map<String, Object>> red = (List<Map<String, Object>>) payload.get("Red");
		String ip = null;
		if (red != null && !red.isEmpty()) {
			ip = (String) red.get(0).get("IPAddress");
		}

		String impresora = (String) payload.get("Printer_Model");

		ReporteInventarioCommand command = new ReporteInventarioCommand(
				nombre,
				ultimoUsuario,
				null, // Fuero will be automatically detected or preserved in Service
				null,
				ip,
				osName,
				procesador,
				ramMb,
				texto(payload.get("RAM_Detalles")),
				texto(payload.get("RAM_Serials")),
				texto(payload.get("Disk_Models")),
				texto(payload.get("Disk_Serials")),
				texto(payload.get("Motherboard_Model")),
				texto(payload.get("Motherboard_SN")),
				texto(payload.get("Monitors")),
				texto(payload.get("Keyboard_Model")),
				texto(payload.get("Mouse_Model")),
				impresora,
				true
		);

		EquipoDetalle equipo = equipoService.registrarInventario(command);
		componenteService.registrarDetectadosDesdeReporte(equipo.id(), command);
		return Map.of("status", "success");
	}

	private String texto(Object valor) {
		return valor instanceof String texto ? texto : null;
	}
}
