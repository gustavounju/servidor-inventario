package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.componentes.GemeloDigitalService;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.GemeloDigitalService.ComparacionComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/v1/equipos/{equipoId}/gemelo-digital")
public class GemeloDigitalController {

	private static final String MODULO_COMPONENTES = "COMPONENTES";
	private static final String PERMISO_VER = "VER";

	private final AuthorizationService authorizationService;
	private final GemeloDigitalService gemeloDigitalService;

	public GemeloDigitalController(AuthorizationService authorizationService, GemeloDigitalService gemeloDigitalService) {
		this.authorizationService = authorizationService;
		this.gemeloDigitalService = gemeloDigitalService;
	}

	@GetMapping("/comparacion")
	public List<ComparacionComponente> comparar(@AuthenticationPrincipal UserDetails userDetails, @PathVariable Long equipoId) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, PERMISO_VER)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para ver el gemelo digital.");
		}
		return gemeloDigitalService.compararEquipo(equipoId);
	}
}
