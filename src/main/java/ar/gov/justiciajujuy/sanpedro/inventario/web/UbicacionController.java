package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.EstadoUbicacion;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.TipoUbicacion;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionService;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionService.GuardarUbicacionCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionService.UbicacionDuplicadaException;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionService.UbicacionDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionService.UbicacionNoEncontradaException;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/v1/ubicaciones")
public class UbicacionController {

	private static final String MODULO_UBICACIONES = "UBICACIONES";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final UbicacionService ubicacionService;

	public UbicacionController(AuthorizationService authorizationService, UbicacionService ubicacionService) {
		this.authorizationService = authorizationService;
		this.ubicacionService = ubicacionService;
	}

	@GetMapping
	public List<UbicacionDetalle> listar(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query,
			@RequestParam(required = false) TipoUbicacion tipo,
			@RequestParam(required = false) EstadoUbicacion estado) {
		exigirPermiso(userDetails, PERMISO_VER);
		return ubicacionService.buscar(query, tipo, estado);
	}

	@PostMapping
	@ResponseStatus(HttpStatus.CREATED)
	public UbicacionDetalle crear(@AuthenticationPrincipal UserDetails userDetails,
			@Valid @RequestBody GuardarUbicacionRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return ubicacionService.crear(request.toCommand());
	}

	@PutMapping("/{id}")
	public UbicacionDetalle actualizar(@AuthenticationPrincipal UserDetails userDetails, @PathVariable Long id,
			@Valid @RequestBody GuardarUbicacionRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return ubicacionService.actualizar(id, request.toCommand());
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_UBICACIONES, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar ubicaciones.");
		}
	}

	@ExceptionHandler(UbicacionNoEncontradaException.class)
	@ResponseStatus(HttpStatus.NOT_FOUND)
	void noEncontrada() {
	}

	@ExceptionHandler(UbicacionDuplicadaException.class)
	@ResponseStatus(HttpStatus.CONFLICT)
	void duplicada() {
	}

	public record GuardarUbicacionRequest(
			@NotBlank @Size(max = 80) String codigo,
			@NotBlank @Size(max = 180) String nombre,
			TipoUbicacion tipo,
			@Size(max = 120) String fuero,
			@Size(max = 120) String responsable,
			@Size(max = 120) String edificio,
			@Size(max = 40) String piso,
			EstadoUbicacion estado,
			@Size(max = 500) String observaciones,
			boolean activo) {

		private GuardarUbicacionCommand toCommand() {
			return new GuardarUbicacionCommand(codigo, nombre, tipo, fuero, responsable, edificio, piso, estado,
					observaciones, activo);
		}
	}
}
